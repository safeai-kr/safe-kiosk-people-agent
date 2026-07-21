from pathlib import Path

from safe_kiosk_people_agent.commands.reload_config import ConfigReloader


FIXTURE = Path(__file__).parents[1] / "fixtures/config/minimal.toml"


def test_config_reload_promotes_atomically_and_increments_generation(tmp_path: Path) -> None:
    active = tmp_path / "config.toml"
    active.write_bytes(FIXTURE.read_bytes())
    candidate = tmp_path / "candidate.toml"
    candidate.write_bytes(FIXTURE.read_bytes())
    first = ConfigReloader(active).apply(candidate)
    second = ConfigReloader(active).apply(candidate)
    assert first.applied and first.active_generation == 1
    assert second.applied and second.active_generation == 2
