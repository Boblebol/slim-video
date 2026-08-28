"""Unit tests for slim_video.estimator module."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from slim_video.estimator import _run_with_progress, estimate_savings


def test_estimate_savings_file_not_found(tmp_path: Path) -> None:
    non_existent = tmp_path / "ghost.mp4"
    res = estimate_savings(non_existent)
    assert res == {"error": "file_empty_or_missing"}


@patch("slim_video.estimator.get_duration")
@patch("slim_video.estimator.get_audio_bitrate")
@patch("slim_video.estimator._run")
@patch("slim_video.estimator._run_with_progress")
def test_estimate_savings_successful(
    mock_run_prog: MagicMock,
    mock_run: MagicMock,
    mock_audio: MagicMock,
    mock_dur: MagicMock,
    tmp_path: Path,
) -> None:
    vid = tmp_path / "vid.mp4"
    vid.write_bytes(b"0" * 10_000)
    mock_dur.return_value = 100.0
    mock_audio.return_value = 0

    # Step 1: create sample_raw.mkv
    def _fake_run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        out_path = Path(cmd[-3])
        out_path.write_bytes(b"0" * 2_000)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    mock_run.side_effect = _fake_run

    # Step 2: create sample_hevc.mkv
    def _fake_run_prog(
        cmd: list[str], duration: float = 0.0, callback: object = None
    ) -> subprocess.CompletedProcess[str]:
        out_path = Path(cmd[-3])
        out_path.write_bytes(b"0" * 400)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    mock_run_prog.side_effect = _fake_run_prog

    cb = MagicMock()
    res = estimate_savings(vid, quality=50, sample_seconds=20, callback=cb)

    assert "error" not in res
    assert res["original_size"] == 10_000
    assert res["estimated_size"] == 2000  # (400 / 2000) * 10_000 = 2000
    assert res["gain_pct"] == 80.0
    assert res["ratio"] == 0.2


@patch("subprocess.Popen")
def test_run_with_progress_success(mock_popen: MagicMock) -> None:
    proc = MagicMock()
    proc.stdout = ["out_time_us=5000000\n", "speed=2.5x\n"]
    proc.wait.return_value = 0
    proc.returncode = 0
    proc.stderr = MagicMock()
    proc.stderr.read.return_value = ""
    mock_popen.return_value = proc

    cb = MagicMock()
    res = _run_with_progress(["ffmpeg", "dummy"], duration=10.0, callback=cb)
    assert res.returncode == 0
    assert cb.called
