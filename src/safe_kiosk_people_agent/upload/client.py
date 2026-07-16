from __future__ import annotations
from pathlib import Path
import httpx
import stat
from typing import Mapping
from .contracts import ContractError, parse_ingest_response
class IngestClient:
    def __init__(self,url:str,token_file:Path,*,client:httpx.AsyncClient|None=None): self.url=url; self.token_file=token_file; self.client=client or httpx.AsyncClient(timeout=30)
    def _read_token(self)->str:
        info=self.token_file.lstat()
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode)!=0o600: raise ContractError('device token file must be mode 0600')
        token=self.token_file.read_text().strip()
        if not __import__('re').fullmatch(r'[A-Za-z0-9_-]{43}',token): raise ContractError('invalid device token')
        return token
    async def post(self,request:Mapping[str,object],device_token:str|None=None)->dict[str,object]:
        token=device_token or self._read_token()
        response=await self.client.post(self.url,json=request,headers={'X-Device-Token':token})
        if response.status_code<200 or response.status_code>=300: raise httpx.HTTPStatusError('ingest failed',request=response.request,response=response)
        metrics = request.get('metrics', [])
        return parse_ingest_response(response.json(), len(metrics) if isinstance(metrics, list) else 0)
