from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Sequence
from ..clock import floor_utc
from ..domain import ConfigSnapshot, MetricEvent, Source, SourceCursor, StateSnapshot, StoredObservationSummary, ReductionBatch, CommitOutcome
from .sqlite import open_sqlite, transaction

def _iso(v:datetime)->str:
    if v.tzinfo is None: raise ValueError("timestamp must be timezone-aware")
    return v.astimezone(timezone.utc).isoformat()
class MetricsStore:
    def __init__(self,path:Path): self.db=open_sqlite(path,"safe_kiosk_people_agent.storage.schema.metrics")
    def source_cursor(self,source:Source)->SourceCursor|None:
        r=self.db.execute("select * from source_cursor where source=?",(source.value,)).fetchone()
        return None if r is None else SourceCursor(source,r['collector_run_id'],r['spool_sequence'],datetime.fromisoformat(r['last_event_time']) if r['last_event_time'] else None)
    def initialize_runtime_state(self,now:datetime,config:ConfigSnapshot)->StateSnapshot:
        anchor=floor_utc(now,300)-timedelta(seconds=300)
        existing=self.load_runtime_state()
        if existing:return existing
        with transaction(self.db):
            self.db.execute("insert into config_snapshot(generation,threshold_version,content_digest,canonical_config_json,state,activation_token,requested_at) values(?,?,?,?,?,?,?)",(config.generation,config.threshold_version,config.content_digest,config.canonical_config_json,'active','genesis',_iso(now)))
            self.db.execute("insert into state_snapshot(snapshot_at,processed_through,canonical_state_json,config_generation) values(?,?,?,?)",(_iso(anchor),_iso(anchor),'{}',config.generation))
            self.db.execute("insert into scheduler_state(singleton,processed_through,last_tick_at) values(1,?,?)",(_iso(anchor),_iso(anchor)))
        return StateSnapshot(anchor,anchor,{},'{}',config.generation)
    def load_runtime_state(self)->StateSnapshot|None:
        r=self.db.execute("select * from state_snapshot order by snapshot_at desc limit 1").fetchone()
        return None if r is None else StateSnapshot(datetime.fromisoformat(r['snapshot_at']),datetime.fromisoformat(r['processed_through']),{},r['canonical_state_json'],r['config_generation'])
    def stage_source_rows(self,rows:Sequence[StoredObservationSummary])->tuple[MetricEvent,...]:
        result=[]
        with transaction(self.db):
            for row in rows:
                payload={"summary_id":row.summary_id,"source":row.source.value,"device_token":row.device_token,"window_start":_iso(row.window_start),"window_end":_iso(row.window_end),"first_observed_at":_iso(row.first_observed_at),"last_observed_at":_iso(row.last_observed_at),"sample_count":row.sample_count,"median_rssi_dbm":row.median_rssi_dbm,"max_rssi_dbm":row.max_rssi_dbm,"frequency_mhz":row.frequency_mhz,"tx_power_dbm":row.tx_power_dbm}
                self.db.execute("insert or ignore into metric_event(source,summary_id,spool_sequence,event_time,payload_json,collector_run_id) values(?,?,?,?,?,?)",(row.source.value,row.summary_id,row.spool_sequence,_iso(row.last_observed_at),json.dumps(payload),row.collector_run_id))
                result.append(MetricEvent(row.source,row.summary_id,row.spool_sequence,row.last_observed_at,row))
        return tuple(result)
    def load_staged_events(self,*,limit:int)->tuple[MetricEvent,...]:
        rows=self.db.execute("select * from metric_event where consumed=0 order by source,spool_sequence limit ?",(limit,)).fetchall()
        result=[]
        for r in rows:
            p=json.loads(r['payload_json']); summary=StoredObservationSummary(p['summary_id'],Source(p['source']),r['collector_run_id'],p['device_token'],datetime.fromisoformat(p['window_start']),datetime.fromisoformat(p['window_end']),datetime.fromisoformat(p['first_observed_at']),datetime.fromisoformat(p['last_observed_at']),p['sample_count'],p['median_rssi_dbm'],p['max_rssi_dbm'],p['frequency_mhz'],p['tx_power_dbm'],r['spool_sequence'])
            result.append(MetricEvent(Source(r['source']),r['summary_id'],r['spool_sequence'],datetime.fromisoformat(r['event_time']),summary))
        return tuple(result)
    def commit_event(self,event:MetricEvent,source_cursor:SourceCursor|None,reduction:ReductionBatch)->CommitOutcome:
        with transaction(self.db):
            row=self.db.execute("select consumed from metric_event where source=? and summary_id=?",(event.source.value,event.summary_id)).fetchone()
            if row is None or row['consumed']: return CommitOutcome(False,source_cursor or SourceCursor(event.source,event.summary.collector_run_id,event.spool_sequence,event.event_time),())
            self.db.execute("update metric_event set consumed=1 where source=? and summary_id=?",(event.source.value,event.summary_id))
            if source_cursor:self.db.execute("insert into source_cursor(source,collector_run_id,spool_sequence,last_event_time) values(?,?,?,?) on conflict(source) do update set collector_run_id=excluded.collector_run_id,spool_sequence=excluded.spool_sequence,last_event_time=excluded.last_event_time",(source_cursor.source.value,source_cursor.collector_run_id,source_cursor.spool_sequence,_iso(source_cursor.last_event_time) if source_cursor.last_event_time else None))
        return CommitOutcome(True,source_cursor or SourceCursor(event.source,event.summary.collector_run_id,event.spool_sequence,event.event_time),())

    def commit_reduction(self, reduction: ReductionBatch) -> None:
        """Persist reducer state, buckets, outbox and cursors atomically."""
        with transaction(self.db):
            for row in reduction.session_rows:
                self.db.execute("insert or replace into active_session(source,device_token,payload_json) values(?,?,?)", (row["source"], row["device_token"], json.dumps(row, sort_keys=True, default=str)))
            for row in reduction.fixed_device_rows:
                self.db.execute("insert or replace into fixed_device(source,device_token,last_observed_at,fixed_until) values(?,?,?,?)", (row["source"], row["device_token"], row["last_observed_at"], row["fixed_until"]))
            for row in reduction.health_rows:
                self.db.execute("insert or replace into source_health(source,health,observed_at) values(?,?,?)", (row["source"], row["health"], row["observed_at"]))
            for bucket in reduction.bucket_rows:
                payload = json.dumps(bucket.to_wire(), sort_keys=True)
                self.db.execute("insert into bucket_metric(bucket_start,bucket_end,payload_json,estimated_people_count,peak_people_count,revision) values(?,?,?,?,?,?) on conflict(bucket_start) do update set bucket_end=excluded.bucket_end,payload_json=excluded.payload_json,estimated_people_count=excluded.estimated_people_count,peak_people_count=excluded.peak_people_count,revision=excluded.revision", (_iso(bucket.bucket_start), _iso(bucket.bucket_end), payload, bucket.estimated_people_count, bucket.peak_people_count, bucket.revision))
            for row in reduction.snapshot_rows:
                self.db.execute("insert into state_snapshot(snapshot_at,processed_through,canonical_state_json,config_generation) values(?,?,?,?)", (row["snapshot_at"], row["processed_through"], row["canonical_state_json"], row["config_generation"]))
            for row in reduction.outbox_rows:
                self.db.execute("insert or replace into upload_outbox(bucket_start,payload_json,state,revision) values(?,?,?,?)", (row["bucket_start"], row["payload_json"], row.get("state", "pending"), row["revision"]))
            for cursor in reduction.source_cursors:
                self.db.execute("insert into source_cursor(source,collector_run_id,spool_sequence,last_event_time) values(?,?,?,?) on conflict(source) do update set collector_run_id=excluded.collector_run_id,spool_sequence=excluded.spool_sequence,last_event_time=excluded.last_event_time", (cursor.source.value, cursor.collector_run_id, cursor.spool_sequence, _iso(cursor.last_event_time) if cursor.last_event_time else None))
            for source, summary_id in reduction.consumed_event_keys:
                self.db.execute("update metric_event set consumed=1 where source=? and summary_id=?", (source.value, summary_id))
