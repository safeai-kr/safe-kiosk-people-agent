from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
from ..domain import KismetCursor, NewObservationSummary, Source, SourceHealth, SourceWatermark, StoredObservationSummary
from .sqlite import open_sqlite, transaction

def _iso(value: datetime) -> str:
    if value.tzinfo is None: raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()

class _Spool:
    source: Source
    def __init__(self, path: Path, package: str) -> None: self.db = open_sqlite(path, package)
    def _append(self, summaries: Sequence[NewObservationSummary], watermark: SourceWatermark, *, generation_id: str | None = None, cursor: KismetCursor | None = None) -> tuple[StoredObservationSummary,...]:
        result=[]
        with transaction(self.db):
            next_seq = self.db.execute("select coalesce(max(spool_sequence),0)+1 from observation_summary").fetchone()[0]
            for summary in summaries:
                row = StoredObservationSummary(summary.summary_id, summary.source, summary.collector_run_id, summary.device_token, summary.window_start, summary.window_end, summary.first_observed_at, summary.last_observed_at, summary.sample_count, summary.median_rssi_dbm, summary.max_rssi_dbm, summary.frequency_mhz, summary.tx_power_dbm, next_seq)
                self.db.execute("insert into observation_summary(summary_id,source,collector_run_id,device_token,window_start,window_end,first_observed_at,last_observed_at,sample_count,median_rssi_dbm,max_rssi_dbm,frequency_mhz,tx_power_dbm,spool_sequence) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (row.summary_id,row.source.value,row.collector_run_id,row.device_token,_iso(row.window_start),_iso(row.window_end),_iso(row.first_observed_at),_iso(row.last_observed_at),row.sample_count,row.median_rssi_dbm,row.max_rssi_dbm,row.frequency_mhz,row.tx_power_dbm,row.spool_sequence))
                result.append(row); next_seq += 1
            self.db.execute("insert into source_watermark(source,collector_run_id,boot_id,caught_up_through,spool_sequence,health,updated_at,updated_boottime_ns,progress_sequence) values(?,?,?,?,?,?,?,?,?) on conflict(source) do update set collector_run_id=excluded.collector_run_id,caught_up_through=excluded.caught_up_through,spool_sequence=excluded.spool_sequence,health=excluded.health,updated_at=excluded.updated_at", (watermark.source.value,watermark.collector_run_id,watermark.boot_id,_iso(watermark.caught_up_through),watermark.spool_sequence,watermark.health.value,_iso(watermark.updated_at),watermark.updated_boottime_ns,watermark.progress_sequence))
            if generation_id is not None and cursor is not None:
                self.db.execute("insert into kismet_generation_cursor(generation_id,ts_sec,ts_usec,rowid_value) values(?,?,?,?) on conflict(generation_id) do update set ts_sec=excluded.ts_sec,ts_usec=excluded.ts_usec,rowid_value=excluded.rowid_value", (generation_id, cursor.ts_sec, cursor.ts_usec, cursor.rowid))
        return tuple(result)
    def read_after(self, sequence:int, limit:int) -> tuple[StoredObservationSummary,...]:
        rows=self.db.execute("select * from observation_summary where spool_sequence>? order by spool_sequence limit ?",(sequence,limit)).fetchall()
        return tuple(StoredObservationSummary(r['summary_id'],Source(r['source']),r['collector_run_id'],r['device_token'],datetime.fromisoformat(r['window_start']),datetime.fromisoformat(r['window_end']),datetime.fromisoformat(r['first_observed_at']),datetime.fromisoformat(r['last_observed_at']),r['sample_count'],r['median_rssi_dbm'],r['max_rssi_dbm'],r['frequency_mhz'],r['tx_power_dbm'],r['spool_sequence']) for r in rows)

    def current_sequence(self) -> int:
        row = self.db.execute("select coalesce(max(spool_sequence), 0) from observation_summary").fetchone()
        return int(row[0])

    def read_watermark(self) -> SourceWatermark | None:
        row = self.db.execute("select * from source_watermark where source=?", (self.source.value,)).fetchone()
        if row is None:
            return None
        return SourceWatermark(self.source, row["collector_run_id"], row["boot_id"], datetime.fromisoformat(row["caught_up_through"]), datetime.fromisoformat(row["caught_up_through"]), row["spool_sequence"], SourceHealth(row["health"]), datetime.fromisoformat(row["updated_at"]), row["updated_boottime_ns"], row["progress_sequence"])

    def close(self) -> None:
        self.db.close()

    def read_cursor(self, generation_id: str) -> KismetCursor | None:
        row = self.db.execute("select generation_id,ts_sec,ts_usec,rowid_value from kismet_generation_cursor where generation_id=?", (generation_id,)).fetchone()
        return None if row is None else KismetCursor(row["generation_id"], row["ts_sec"], row["ts_usec"], row["rowid_value"])

class WifiSpool(_Spool):
    source=Source.WIFI
    def __init__(self,path:Path): super().__init__(path,"safe_kiosk_people_agent.storage.schema.wifi")
    def append_poll(self,generation_id:str,next_cursor:KismetCursor,summaries:Sequence[NewObservationSummary],watermark:SourceWatermark)->tuple[StoredObservationSummary,...]: return self._append(summaries,watermark,generation_id=generation_id,cursor=next_cursor)

class BleSpool(_Spool):
    source=Source.BLE
    def __init__(self,path:Path): super().__init__(path,"safe_kiosk_people_agent.storage.schema.ble")
    def append_window(self,summaries:Sequence[NewObservationSummary],watermark:SourceWatermark)->tuple[StoredObservationSummary,...]: return self._append(summaries,watermark)
