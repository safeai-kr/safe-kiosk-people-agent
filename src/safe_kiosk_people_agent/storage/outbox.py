from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping
from ..domain import BucketMetric, OutboxState
from .sqlite import open_sqlite, transaction

@dataclass(frozen=True)
class OutboxRow:
    bucket_start:str; payload:Mapping[str,object]; revision:int; state:OutboxState

class OutboxStore:
    def __init__(self,path:Path): self.db=open_sqlite(path,'safe_kiosk_people_agent.storage.schema.metrics')
    def upsert(self,metric:BucketMetric)->None:
        payload=metric.to_wire(); start=str(payload['bucket_start'])
        with transaction(self.db):
            self.db.execute('insert into upload_outbox(bucket_start,payload_json,state,revision) values(?,?,?,?) on conflict(bucket_start) do update set payload_json=excluded.payload_json, revision=excluded.revision, state=case when excluded.revision>upload_outbox.revision then ? else upload_outbox.state end',(start,json.dumps(payload,separators=(',',':')),OutboxState.PENDING.value,metric.revision,OutboxState.PENDING.value))
    def get(self,bucket_start:str)->OutboxRow|None:
        row=self.db.execute('select * from upload_outbox where bucket_start=?',(bucket_start,)).fetchone()
        return None if row is None else OutboxRow(row['bucket_start'],json.loads(row['payload_json']),row['revision'],OutboxState(row['state']))
    def claim_batch(self,limit:int=288)->tuple[OutboxRow,...]:
        rows=self.db.execute("select * from upload_outbox where state='pending' order by bucket_start limit ?",(limit,)).fetchall()
        return tuple(OutboxRow(r['bucket_start'],json.loads(r['payload_json']),r['revision'],OutboxState(r['state'])) for r in rows)
    def mark_terminal(self,bucket_start:str,revision:int,reason:str)->bool:
        with transaction(self.db):
            cur=self.db.execute("update upload_outbox set state='terminal_rejected' where bucket_start=? and revision=? and state='pending'",(bucket_start,revision))
        return cur.rowcount==1
    def apply_server_result(self,bucket_start:str,sent_revision:int,result:str)->bool:
        state=OutboxState.TERMINAL_REJECTED if result=='rejected' else OutboxState.DELIVERED
        with transaction(self.db):
            cur=self.db.execute('update upload_outbox set state=? where bucket_start=? and revision=? and state=?',(state.value,bucket_start,sent_revision,OutboxState.PENDING.value))
        return cur.rowcount==1
