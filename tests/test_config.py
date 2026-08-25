"""Unit tests for slim_video.config module."""

from __future__ import annotations

from pathlib import Path

from slim_video.config import ConfigManager


def test_config_defaults(tmp_path: Path) -> None:
    mgr = ConfigManager(tmp_path / "test_config.json")
    cfg = mgr.load()
    assert cfg.min_gain_percent == 10.0
    assert cfg.sample_duration_seconds == 20
    assert cfg.quality == 50
    assert cfg.auto_sample_test is True
    assert cfg.ssd_staging is False
    assert cfg.temp_dir == "/tmp/slim-video"


def test_config_set_and_get(tmp_path: Path) -> None:
    mgr = ConfigManager(tmp_path / "test_config.json")
    k, v = mgr.set("min_gain_percent", "15.5")
    assert k == "min_gain_percent"
    assert v == 15.5
    assert mgr.get("min_gain_percent") == 15.5

    _, v2 = mgr.set("sample_duration_seconds", "30")
    assert v2 == 30
    assert mgr.get("sample_duration_seconds") == 30

    _, v3 = mgr.set("auto_sample_test", "false")
    assert v3 is False
    assert mgr.get("auto_sample_test") is False

    _, v4 = mgr.set("ssd_staging", "true")
    assert v4 is True
    assert mgr.get("ssd_staging") is True

    _, v5 = mgr.set("temp_dir", "/tmp/my-staging")
    assert v5 == "/tmp/my-staging"
    assert mgr.get("temp_dir") == "/tmp/my-staging"


def test_config_reset(tmp_path: Path) -> None:
    mgr = ConfigManager(tmp_path / "test_config.json")
    mgr.set("min_gain_percent", "25.0")
    mgr.set("ssd_staging", "true")
    assert mgr.get("min_gain_percent") == 25.0
    assert mgr.get("ssd_staging") is True

    reset_cfg = mgr.reset()
    assert reset_cfg.min_gain_percent == 10.0
    assert reset_cfg.ssd_staging is False
    assert mgr.get("min_gain_percent") == 10.0
    assert mgr.get("ssd_staging") is False
