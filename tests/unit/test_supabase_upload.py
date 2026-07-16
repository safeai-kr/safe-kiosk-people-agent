from datetime import datetime, timezone
import httpx
from safe_kiosk_people_agent.domain import Source
from safe_kiosk_people_agent.metrics import MetricBucket
from safe_kiosk_people_agent.upload import SupabaseUploader
def bucket(): return MetricBucket(datetime(2026,1,1,tzinfo=timezone.utc),2,2,3,(Source.WIFI,))
def test_upload_has_idempotency_and_auth():
    requests=[]
    def handler(request): requests.append(request); return httpx.Response(200,request=request)
    result=SupabaseUploader('https://example.supabase.co','/functions/v1/ingest','secret',client=httpx.Client(transport=httpx.MockTransport(handler))).upload([bucket()])
    assert result.sent==1 and requests[0].headers['idempotency-key'] and requests[0].headers['authorization']=='Bearer secret'
