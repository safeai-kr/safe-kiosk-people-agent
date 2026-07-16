from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from ..storage.outbox import OutboxStore
@dataclass(frozen=True)
class UploadRun:
    delivered:tuple[str,...]; terminal_rejected:tuple[str,...]; retry_pending:bool
class Uploader:
    def __init__(self,store:OutboxStore,client): self.store=store; self.client=client
    async def run_once(self,now:datetime)->UploadRun:
        rows=self.store.claim_batch(288)
        if not rows:return UploadRun((),(),False)
        request={'metrics':[dict(row.payload) for row in rows]}
        response=await self.client.post(request)
        delivered:list[str]=[]; terminal:list[str]=[]
        for result in response['metrics']:
            row=rows[result['index']]; bucket=row.bucket_start
            if self.store.apply_server_result(bucket,row.revision,result['result']):
                (terminal if result['result']=='rejected' else delivered).append(bucket)
        return UploadRun(tuple(delivered),tuple(terminal),False)
    async def run(self,stop)->None:
        import asyncio
        while not stop.is_set():
            await self.run_once(datetime.now().astimezone())
            try: await asyncio.wait_for(stop.wait(),300)
            except asyncio.TimeoutError: pass
    async def run_resilient(self,stop)->None:
        import asyncio
        while not stop.is_set():
            try: await self.run(stop)
            except Exception: await asyncio.sleep(10)
