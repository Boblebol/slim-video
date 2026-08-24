"""Unit tests for hevc_cli.config module."""

from __future__ import annotations

from pathlib import Path

from hevc_cli.config import ConfigManager


def test_config_defaults(tmp_path: Path) -> None:
    mgr = ConfigManager(tmp_path / "test_config.json")
    cfg = mgr.load()
    assert cfg.min_gain_percent == 10.0
    assert cfg.sample_duration_seconds == 20
    assert cfg.quality == 50
    assert cfg.auto_sample_test is True


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


def test_config_reset(tmp_path: Path) -> None:
    mgr = ConfigManager(tmp_path / "test_config.json")
    mgr.set("min_gain_percent", "25.0")
    assert mgr.get("min_gain_percent") == 25.0

    reset_cfg = mgr.reset()
    assert reset_cfg.min_gain_percent == 10.0
    assert mgr.get("min_gain_percent") == 10.0
