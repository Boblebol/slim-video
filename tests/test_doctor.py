"""Unit tests for hevc_cli.doctor diagnostic module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from hevc_cli.doctor import (
    check_curses_terminal,
    check_ffmpeg_binary,
    check_ffprobe_binary,
    check_platform,
    check_python_version,
    check_temp_storage,
    check_videotoolbox_support,
    run_all_doctor_checks,
)


def test_check_python_version() -> None:
    res = check_python_version()
    assert res.passed is True
    assert "Python" in res.details


def test_check_platform() -> None:
    res = check_platform()
    assert res.passed is True
    assert len(res.details) > 0


def test_check_temp_storage() -> None:
    res = check_temp_storage()
    assert res.passed is True
    assert "OK" in res.details


def test_check_curses_terminal() -> None:
    res = check_curses_terminal()
    assert res.passed is True


@patch("hevc_cli.doctor.shutil.which")
def test_check_ffmpeg_binary_missing(mock_which: MagicMock) -> None:
    mock_which.return_value = None
    res = check_ffmpeg_binary()
    assert res.passed is False
    assert "Not found" in res.details


@patch("hevc_cli.doctor.shutil.which")
def test_check_ffprobe_binary_missing(mock_which: MagicMock) -> None:
    mock_which.return_value = None
    res = check_ffprobe_binary()
    assert res.passed is False
    assert "Not found" in res.details


@patch("hevc_cli.doctor.subprocess.run")
@patch("hevc_cli.doctor.shutil.which")
def test_check_videotoolbox_support(mock_which: MagicMock, mock_run: MagicMock) -> None:
    mock_which.return_value = "/opt/homebrew/bin/ffmpeg"
    mock_run.return_value = MagicMock(stdout="hevc_videotoolbox\nlibx265", returncode=0)

    res = check_videotoolbox_support()
    assert res.passed is True
    assert "hevc_videotoolbox" in res.details


def test_run_all_doctor_checks() -> None:
    checks = run_all_doctor_checks(include_benchmark=False)
    assert len(checks) >= 6
    for c in checks:
        assert c.name
