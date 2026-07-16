from datetime import datetime
from safe_kiosk_people_agent.collectors.summary import TenSecondSummarizer, TokenizedObservation, make_summary_id
from safe_kiosk_people_agent.domain import Source

def utc(value: str) -> datetime: return datetime.fromisoformat(value.replace("Z", "+00:00"))
def obs(origin: str, at: str, rssi: int) -> TokenizedObservation: return TokenizedObservation(origin, Source.WIFI, "t"*64, utc(at), rssi, None, None)
def test_summary_uses_first_last_median_max_and_stable_id() -> None:
    summarizer = TenSecondSummarizer(source=Source.WIFI, collector_run_id="run-1")
    summarizer.add(obs("origin-2", "2026-07-14T12:00:08Z", -61)); summarizer.add(obs("origin-1", "2026-07-14T12:00:01Z", -71)); summarizer.add(obs("origin-3", "2026-07-14T12:00:05Z", -66))
    [summary] = summarizer.flush_through(utc("2026-07-14T12:00:10Z"))
    assert summary.first_observed_at == utc("2026-07-14T12:00:01Z") and summary.last_observed_at == utc("2026-07-14T12:00:08Z")
    assert (summary.sample_count, summary.median_rssi_dbm, summary.max_rssi_dbm) == (3, -66, -61)
    assert summary.summary_id == make_summary_id(Source.WIFI, "t"*64, utc("2026-07-14T12:00:00Z"), ["origin-1","origin-2","origin-3"])
