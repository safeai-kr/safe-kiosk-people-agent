from pathlib import Path


def test_post_install_harness_exposes_expected_contract() -> None:
    root = Path(__file__).parents[2]
    runner = (root / "tests/post_install/verify.py").read_text()
    assert "ALLOW_PI_POST_INSTALL" in runner
    assert "aarch64" in runner
    for value in ("expected-commit", "expected-bundle-sha256", "current", "output"):
        assert value in runner
    assert "systemctl" in runner and "skwifi0" in runner and "2501" in runner
