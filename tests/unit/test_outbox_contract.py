from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID
from safe_kiosk_people_agent.domain import BucketMetric, Source, ProtocolSourceDetail, SensorStatus, SourceHealth
from safe_kiosk_people_agent.storage.outbox import OutboxStore
from safe_kiosk_people_agent.upload.contracts import build_ingest_request, ContractError, parse_ingest_response

def metric(revision=1):
    return BucketMetric(datetime(2026,1,1,tzinfo=timezone.utc),datetime(2026,1,1,0,5,tzinfo=timezone.utc),1,2,3,1,Decimal('10'),Decimal('1'),1,1,Decimal('0.9'),(),{Source.WIFI: ProtocolSourceDetail(1,3,1,Decimal('10'),Decimal('1'),0,0,0)},'v1','m1',revision,datetime(2026,1,1,0,5,tzinfo=timezone.utc))
def test_outbox_new_revision_reopens_terminal(tmp_path: Path):
    store=OutboxStore(tmp_path/'metrics.sqlite'); store.upsert(metric(1)); assert store.mark_terminal('2026-01-01T00:00:00+00:00',1,'invalid')
    store.upsert(metric(2)); row=store.get('2026-01-01T00:00:00+00:00'); assert row is not None and row.state.value=='pending'
def test_contract_limits_and_indexes():
    payload=build_ingest_request(UUID('00000000-0000-4000-8000-000000000101'), SensorStatus(datetime.now(timezone.utc),SourceHealth.HEALTHY,SourceHealth.HEALTHY,SourceHealth.HEALTHY,SourceHealth.HEALTHY,SourceHealth.HEALTHY,None,None,None,None,{},Decimal('0'),0,0,0,None,'v1','m1'), [metric()])
    assert payload['sensor_id'].startswith('0000')
    assert parse_ingest_response({'sensor_id':'x','received_at':'now','status_result':'inserted','metrics':[{'index':0,'result':'inserted'}]},1)['status_result']=='inserted'
    try: build_ingest_request(UUID(int=0),payload['status'],[metric()]*289)
    except ContractError: pass
    else: raise AssertionError('expected size limit')
