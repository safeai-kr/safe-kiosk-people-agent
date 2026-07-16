from __future__ import annotations
from dataclasses import dataclass
import hashlib
import time
from typing import Callable, Iterable
import httpx
from ..metrics.worker import MetricBucket
@dataclass(frozen=True)
class UploadResult:
    sent:int; retryable_failures:int; terminal_failures:int
class SupabaseUploader:
    def __init__(self,url:str,ingest_path:str,device_token:str,*,client:httpx.Client|None=None,retries:int=3,sleep:Callable[[float],None]=time.sleep):
        self.url=url.rstrip('/')+('/' if not ingest_path.startswith('/') else '')+ingest_path.lstrip('/'); self.token=device_token; self.client=client or httpx.Client(timeout=30); self.retries=retries; self.sleep=sleep
    def _key(self,bucket:MetricBucket)->str: return hashlib.sha256(f'{bucket.bucket_start.isoformat()}:{bucket.estimated_people_count}:{bucket.observation_count}'.encode()).hexdigest()
    def upload(self,buckets:Iterable[MetricBucket])->UploadResult:
        sent=retryable=terminal=0
        for bucket in buckets:
            payload={'bucket_start':bucket.bucket_start.isoformat(),'estimated_people_count':bucket.estimated_people_count,'peak_people_count':bucket.peak_people_count,'observation_count':bucket.observation_count,'sources':[s.value for s in bucket.sources]}
            for attempt in range(self.retries+1):
                try:
                    response=self.client.post(self.url,json=payload,headers={'Authorization':f'Bearer {self.token}','Idempotency-Key':self._key(bucket)})
                    if 200<=response.status_code<300: sent+=1; break
                    if response.status_code in (408,425,429) or response.status_code>=500: raise httpx.HTTPStatusError('retryable',request=response.request,response=response)
                    terminal+=1; break
                except (httpx.TimeoutException,httpx.NetworkError,httpx.HTTPStatusError):
                    if attempt>=self.retries: retryable+=1
                    else: self.sleep(min(30.0,2**attempt))
        return UploadResult(sent,retryable,terminal)
