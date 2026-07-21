from safe_kiosk_people_agent.recovery.ownership import HolderState, InterfaceOwnershipInspector


def test_zombie_is_defunct_and_foreign_blocks_recovery() -> None:
    inspector = InterfaceOwnershipInspector()
    assert inspector.classify({"pid": 412, "state": "Z", "expected": True}) is HolderState.DEFUNCT
    report = inspector.inspect([{"pid": 99, "state": "S", "expected": False}])
    assert report.state is HolderState.FOREIGN
