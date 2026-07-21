from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping
from ..domain import BucketMetric, OutboxState, ProtocolSourceDetail, Source
from datetime import datetime, timezone
from decimal import Decimal
from .sqlite import open_sqlite, transaction

@dataclass(frozen=True)
class OutboxRow:
    bucket_start:str; payload:Mapping[str,object]; revision:int; state:OutboxState; metric:BucketMetric


def _metric_from_payload(payload: Mapping[str, object], revision: int) -> BucketMetric:
    details = {}
    raw_details = payload.get("source_detail", {})
    if isinstance(raw_details, Mapping):
        for source in Source:
            raw = raw_details.get(source.value, {})
            if isinstance(raw, Mapping):
                details[source] = ProtocolSourceDetail(int(str(raw.get("inside_tick_count", 0))), int(str(raw.get("foot_traffic_count", 0))), int(str(raw.get("entry_count", 0))), Decimal(str(raw.get("dwell_seconds_sum", 0))), Decimal(str(raw.get("completed_dwell_session_count", 0))), int(str(raw.get("timeout_closed_count", 0))), int(str(raw.get("unconfirmed_entry_count", 0))), int(str(raw.get("interrupted_session_count", 0))))
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(str(payload["bucket_start"]))
    end = datetime.fromisoformat(str(payload["bucket_end"]))
    quality = payload.get("quality_flags", [])
    quality_values = quality if isinstance(quality, (list, tuple)) else []
    return BucketMetric(start, end, int(str(payload["estimated_people_count"])), int(str(payload["peak_people_count"])), int(str(payload["foot_traffic_count"])), int(str(payload["entry_count"])), Decimal(str(payload["dwell_seconds_sum"])), Decimal(str(payload["completed_dwell_session_count"])), int(str(payload["wifi_observation_count"])), int(str(payload["ble_observation_count"])), Decimal(str(payload["confidence_score"])), tuple(str(v) for v in quality_values), details, str(payload["threshold_version"]), str(payload["metric_version"]), revision, datetime.fromisoformat(str(payload.get("generated_at", now.isoformat()))))

class OutboxStore:
    def __init__(self,path:Path): self.db=open_sqlite(path,'safe_kiosk_people_agent.storage.schema.metrics')
    def upsert(self,metric:BucketMetric)->None:
        payload=metric.to_wire(); start=str(payload['bucket_start'])
        with transaction(self.db):
            self.db.execute('insert into upload_outbox(bucket_start,payload_json,state,revision) values(?,?,?,?) on conflict(bucket_start) do update set payload_json=excluded.payload_json, revision=excluded.revision, state=case when excluded.revision>upload_outbox.revision then ? else upload_outbox.state end',(start,json.dumps(payload,separators=(',',':')),OutboxState.PENDING.value,metric.revision,OutboxState.PENDING.value))
    def get(self,bucket_start:str)->OutboxRow|None:
        row=self.db.execute('select * from upload_outbox where bucket_start=?',(bucket_start,)).fetchone()
        return None if row is None else OutboxRow(row['bucket_start'],json.loads(row['payload_json']),row['revision'],OutboxState(row['state']),_metric_from_payload(json.loads(row['payload_json']), row['revision']))
    def claim_batch(self,limit:int=288)->tuple[OutboxRow,...]:
        rows=self.db.execute("select * from upload_outbox where state='pending' order by bucket_start limit ?",(limit,)).fetchall()
        return tuple(OutboxRow(r['bucket_start'],json.loads(r['payload_json']),r['revision'],OutboxState(r['state']),_metric_from_payload(json.loads(r['payload_json']), r['revision'])) for r in rows)

    def claim_ready(self, now: datetime, limit: int = 288) -> tuple[OutboxRow, ...]:
        return self.claim_batch(min(limit, 288))

    def pending_count(self) -> int:
        return int(self.db.execute("select count(*) from upload_outbox where state='pending'").fetchone()[0])
    def mark_terminal(self,bucket_start:str,revision:int,reason:str)->bool:
        with transaction(self.db):
            cur=self.db.execute("update upload_outbox set state='terminal_rejected' where bucket_start=? and revision=? and state='pending'",(bucket_start,revision))
        return cur.rowcount==1
    def apply_server_result(self,bucket_start:str,sent_revision:int,result:str)->bool:
        state=OutboxState.TERMINAL_REJECTED if result=='rejected' else OutboxState.DELIVERED
        with transaction(self.db):
            cur=self.db.execute('update upload_outbox set state=? where bucket_start=? and revision=? and state=?',(state.value,bucket_start,sent_revision,OutboxState.PENDING.value))
        return cur.rowcount==1
