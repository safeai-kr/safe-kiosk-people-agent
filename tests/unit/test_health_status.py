from pathlib import Path
from safe_kiosk_people_agent.health.recovery_counts import RecoveryCountStore
def test_recovery_counts_round_trip(tmp_path:Path):
    store=RecoveryCountStore(tmp_path/'counts.json'); values={k:1 for k in store.COUNTERS};store.publish_as_root({'lifetime_counts':values});assert store.read_lifetime_counts()==values
