from pathlib import Path
from safe_kiosk_people_agent.domain import ReductionBatch, Source, SourceCursor
from safe_kiosk_people_agent.storage.metrics import MetricsStore
from tests.unit.test_spool_idempotency import summary

def test_duplicate_metric_commit_is_idempotent(tmp_path: Path) -> None:
    store=MetricsStore(tmp_path/'metrics.sqlite'); row=summary(); [event]=store.stage_source_rows((__import__('safe_kiosk_people_agent.domain',fromlist=['StoredObservationSummary']).StoredObservationSummary(row.summary_id,row.source,row.collector_run_id,row.device_token,row.window_start,row.window_end,row.first_observed_at,row.last_observed_at,row.sample_count,row.median_rssi_dbm,row.max_rssi_dbm,row.frequency_mhz,row.tx_power_dbm,1),))
    cursor=SourceCursor(Source.WIFI,'run',1,event.event_time)
    reduction=ReductionBatch((),(),(),(),(),())
    assert store.commit_event(event,cursor,reduction).applied
    assert not store.commit_event(event,cursor,reduction).applied
