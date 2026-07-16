from __future__ import annotations
from uuid import UUID
from typing import Mapping, Sequence
from ..domain import BucketMetric, SensorStatus
class ContractError(ValueError): pass
def build_ingest_request(sensor_id:UUID,status:SensorStatus,metrics:Sequence[BucketMetric])->dict[str,object]:
    if len(metrics)>288: raise ContractError('metrics must contain at most 288 rows')
    return {'sensor_id':str(sensor_id),'status':status.to_wire(),'metrics':[dict(m.to_wire()) for m in metrics]}
def parse_ingest_response(value:object,expected_count:int)->dict[str,object]:
    if not isinstance(value,Mapping) or not isinstance(value.get('metrics'),list): raise ContractError('invalid ingest response')
    results=value['metrics']
    if len(results)!=expected_count: raise ContractError('response result count mismatch')
    seen=[]
    for result in results:
        if not isinstance(result,Mapping) or not isinstance(result.get('index'),int) or result['index']<0 or result['index']>=expected_count: raise ContractError('invalid result index')
        if result['index'] in seen or result.get('result') not in {'inserted','updated','duplicate','superseded','rejected'}: raise ContractError('invalid result')
        seen.append(result['index'])
    if sorted(seen)!=list(range(expected_count)): raise ContractError('incomplete result indexes')
    return {'sensor_id':value.get('sensor_id'),'received_at':value.get('received_at'),'status_result':value.get('status_result'),'metrics':results}
