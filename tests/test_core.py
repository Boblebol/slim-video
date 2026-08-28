"""Unit tests for slim_video.core and slim_video.probing modules.

Run with:
    pytest tests/ -v
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from slim_video.core import (
    DEFAULT_QUALITY,
    SUPPORTED_EXTENSIONS,
    find_h264_candidates,
    find_video_files,
    get_audio_summary,
    get_duration,
    get_fps,
    get_resolution,
    get_video_codec,
    is_h264_codec,
    is_hevc_codec,
    transcode,
)

# ---------------------------------------------------------------------------
# Codec checking helpers
# ---------------------------------------------------------------------------


def test_is_h264_codec() -> None:
    assert is_h264_codec("h264") is True
    assert is_h264_codec("H264") is True
    assert is_h264_codec("avc") is True
    assert is_h264_codec("avc1") is True
    assert is_h264_codec("x264") is True
    assert is_h264_codec("hevc") is False
    assert is_h264_codec("vp9") is False
    assert is_h264_codec(None) is False


def test_is_hevc_codec() -> None:
    assert is_hevc_codec("hevc") is True
    assert is_hevc_codec("HEVC") is True
    assert is_hevc_codec("h265") is True
    assert is_hevc_codec("hvc1") is True
    assert is_hevc_codec("x265") is True
    assert is_hevc_codec("h264") is False
    assert is_hevc_codec(None) is False


# ---------------------------------------------------------------------------
# find_video_files & find_h264_candidates
# ---------------------------------------------------------------------------


def test_find_video_files_single_file(tmp_path: Path) -> None:
    video = tmp_path / "movie.mp4"
    video.touch()
    result = find_video_files(video)
    assert result == [video]


def test_find_video_files_unsupported_extension(tmp_path: Path) -> None:
    txt = tmp_path / "notes.txt"
    txt.touch()
    assert find_video_files(txt) == []


def test_find_video_files_recursive(tmp_path: Path) -> None:
    sub = tmp_path / "season_1"
    sub.mkdir()
    ep1 = sub / "ep01.mkv"
    ep2 = sub / "ep02.mp4"
    nfo = sub / "ep01.nfo"
    ep1.touch()
    ep2.touch()
    nfo.touch()

    found = find_video_files(tmp_path)
    assert set(found) == {ep1, ep2}


def test_find_video_files_excludes_quarantine(tmp_path: Path) -> None:
    quarantine = tmp_path / "_originals_to_delete"
    quarantine.mkdir()
    old_video = quarantine / "old.mp4"
    old_video.touch()

    active_video = tmp_path / "new.mp4"
    active_video.touch()

    found = find_video_files(tmp_path)
    assert found == [active_video]


def test_find_video_files_empty_dir(tmp_path: Path) -> None:
    assert find_video_files(tmp_path) == []


@patch("slim_video.probing.get_video_codec")
def test_find_h264_candidates(mock_codec: MagicMock, tmp_path: Path) -> None:
    h264_file = tmp_path / "film_h264.mp4"
    hevc_file = tmp_path / "film_hevc.mkv"
    h264_file.touch()
    hevc_file.touch()

    def _codec_lookup(p: Path) -> str:
        return "h264" if "h264" in p.name else "hevc"

    mock_codec.side_effect = _codec_lookup

    candidates, already_hevc = find_h264_candidates(tmp_path)
    assert candidates == [h264_file]
    assert already_hevc == [hevc_file]


# ---------------------------------------------------------------------------
# Metadata Probing
# ---------------------------------------------------------------------------


@patch("slim_video.probing._run")
def test_get_video_codec_hevc(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = MagicMock(stdout="hevc\n", returncode=0)
    result = get_video_codec(tmp_path / "video.mkv")
    assert result == "hevc"


@patch("slim_video.probing._run")
def test_get_video_codec_h264(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = MagicMock(stdout="h264\n", returncode=0)
    result = get_video_codec(tmp_path / "video.mp4")
    assert result == "h264"


@patch("slim_video.probing._run")
def test_get_video_codec_empty(mock_run: MagicMock, tmp_path: Path) -> None:
    mock_run.return_value = MagicMock(stdout="\n", returncode=0)
    result = get_video_codec(tmp_path / "video.mp4")
    assert result is None


@patch("slim_video.probing._ffprobe_field")
def test_get_duration_valid(mock_probe: MagicMock, tmp_path: Path) -> None:
    mock_probe.return_value = "3600.5"
    assert get_duration(tmp_path / "video.mkv") == pytest.approx(3600.5)


@patch("slim_video.probing._ffprobe_field")
def test_get_duration_invalid(mock_probe: MagicMock, tmp_path: Path) -> None:
    mock_probe.return_value = None
    assert get_duration(tmp_path / "video.mkv") == 0.0


@patch("slim_video.probing._ffprobe_field")
def test_get_resolution(mock_probe: MagicMock, tmp_path: Path) -> None:
    mock_probe.side_effect = ["1920", "1080"]
    assert get_resolution(tmp_path / "v.mp4") == "1920x1080"


@patch("slim_video.probing._ffprobe_field")
def test_get_fps(mock_probe: MagicMock, tmp_path: Path) -> None:
    mock_probe.return_value = "24000/1001"
    assert get_fps(tmp_path / "v.mp4") == pytest.approx(23.976)


@patch("slim_video.probing._ffprobe_field")
def test_get_audio_summary(mock_probe: MagicMock, tmp_path: Path) -> None:
    mock_probe.side_effect = ["aac", "6"]
    assert get_audio_summary(tmp_path / "v.mp4") == "AAC 6ch"


# ---------------------------------------------------------------------------
# Transcoding & Quarantine
# ---------------------------------------------------------------------------


@patch("slim_video.transcoder._run_with_progress")
def test_transcode_success(mock_run: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "test_video.mp4"
    src.write_bytes(b"0" * 1000)

    def _side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
        temp_out = src.with_name(f".tmp_{src.stem}.hevc.mkv")
        temp_out.write_bytes(b"1" * 500)
        return MagicMock(returncode=0, stderr="")

    mock_run.side_effect = _side_effect

    result = transcode(src, library_root=tmp_path, quality=DEFAULT_QUALITY)

    assert result["status"] == "ok"
    assert result["output_size"] == 500
    final_output = Path(result["output_path"])
    assert final_output.exists()
    assert final_output.name == "test_video.hevc.mkv"

    # Verify original was moved to quarantine
    assert not src.exists()
    quarantine = Path(result["quarantine_path"])
    assert quarantine.exists()
    assert quarantine.name == "test_video.mp4"
    assert "_originals_to_delete" in str(quarantine)


@patch("slim_video.transcoder._run_with_progress")
def test_transcode_success_delete_original(mock_run: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "test_delete.mp4"
    src.write_bytes(b"0" * 1000)

    def _side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
        temp_out = src.with_name(f".tmp_{src.stem}.hevc.mkv")
        temp_out.write_bytes(b"1" * 500)
        return MagicMock(returncode=0, stderr="")

    mock_run.side_effect = _side_effect

    result = transcode(src, library_root=tmp_path, quality=DEFAULT_QUALITY, delete_original=True)

    assert result["status"] == "ok"
    assert result["output_size"] == 500
    assert result["deleted_original"] is True
    assert result["quarantine_path"] is None

    final_output = Path(result["output_path"])
    assert final_output.exists()
    assert final_output.name == "test_delete.hevc.mkv"


@patch("slim_video.transcoder._run_with_progress")
def test_transcode_success_with_staging_dir(mock_run: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "test_staging.mp4"
    src.write_bytes(b"0" * 1000)
    staging_dir = tmp_path / "custom_staging"

    def _side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
        temp_out = staging_dir / f".tmp_{src.stem}.hevc.mkv"
        temp_out.write_bytes(b"1" * 400)
        return MagicMock(returncode=0, stderr="")

    mock_run.side_effect = _side_effect

    result = transcode(
        src,
        library_root=tmp_path,
        quality=DEFAULT_QUALITY,
        staging_dir=staging_dir,
    )

    assert result["status"] == "ok"
    assert result["output_size"] == 400
    final_output = Path(result["output_path"])
    assert final_output.exists()
    assert final_output.name == "test_staging.hevc.mkv"
    assert final_output.parent == tmp_path

    # Verify staging temp file is cleaned up after move
    assert not (staging_dir / f".tmp_{src.stem}.hevc.mkv").exists()


def test_transcode_source_not_found(tmp_path: Path) -> None:
    non_existent = tmp_path / "ghost.mp4"
    result = transcode(non_existent, library_root=tmp_path)
    assert result["status"] == "error"
    assert "does not exist" in result["error_message"]


@patch("shutil.disk_usage")
def test_transcode_insufficient_staging_disk_space(
    mock_disk_usage: MagicMock, tmp_path: Path
) -> None:
    src = tmp_path / "large_video.mp4"
    src.write_bytes(b"0" * 1000)
    staging_dir = tmp_path / "low_space_staging"

    # Free space: 500 bytes, but required is 2x 1000 = 2000 bytes
    mock_disk_usage.return_value = (10000, 9500, 500)

    result = transcode(src, library_root=tmp_path, staging_dir=staging_dir)
    assert result["status"] == "error"
    assert "Insufficient disk space" in result["error_message"]
    assert "requires at least 2x" in result["error_message"]


@patch("slim_video.transcoder._run_with_progress")
def test_transcode_status_callback(mock_run: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "callback_video.mp4"
    src.write_bytes(b"0" * 1000)
    staging_dir = tmp_path / "cb_staging"
    statuses: list[str] = []

    def _side_effect(cmd: list[str], **kwargs: Any) -> MagicMock:
        temp_out = staging_dir / f".tmp_{src.stem}.hevc.mkv"
        temp_out.write_bytes(b"1" * 400)
        return MagicMock(returncode=0, stderr="")

    mock_run.side_effect = _side_effect

    result = transcode(
        src,
        library_root=tmp_path,
        staging_dir=staging_dir,
        status_callback=lambda msg: statuses.append(msg),
    )

    assert result["status"] == "ok"
    assert len(statuses) > 0
    assert any("disk space" in s.lower() for s in statuses)
    assert any("encoding" in s.lower() for s in statuses)
    assert any("transferring" in s.lower() or "moving" in s.lower() for s in statuses)


def test_build_transcode_command(tmp_path: Path) -> None:
    from slim_video.transcoder import build_transcode_command

    src = tmp_path / "in.mp4"
    dst = tmp_path / "out.mkv"

    vt_cmd = build_transcode_command(src, dst, quality=48, encoder="hevc_videotoolbox")
    assert "hevc_videotoolbox" in vt_cmd
    assert "-q:v" in vt_cmd
    assert "48" in vt_cmd
    assert "-spatial_aq" in vt_cmd
    assert "p010le" in vt_cmd

    cpu_cmd = build_transcode_command(src, dst, encoder="libx265")
    assert "libx265" in cpu_cmd
    assert "-crf" in cpu_cmd
    assert "22" in cpu_cmd
    assert "yuv420p10le" in cpu_cmd


@patch("subprocess.Popen")
def test_run_with_progress_exception_cleanup(mock_popen: MagicMock) -> None:
    from slim_video.estimator import _run_with_progress

    mock_proc = MagicMock()
    mock_proc.stdout = ["out_time_us=50000000\n"]  # Trigger callback
    mock_proc.wait.return_value = 0
    mock_proc.returncode = 0
    mock_proc.stderr = MagicMock()
    mock_proc.stderr.read.return_value = ""
    mock_popen.return_value = mock_proc

    def _faulty_callback(pct: float, elapsed: float, speed: str) -> None:
        raise KeyboardInterrupt("Simulated Ctrl+C")

    with pytest.raises(KeyboardInterrupt):
        _run_with_progress(["ffmpeg"], duration=100.0, callback=_faulty_callback)

    # Verify process termination was attempted
    mock_proc.terminate.assert_called_once()


def test_history_capping(tmp_path: Path) -> None:
    from slim_video.history import MAX_HISTORY_TESTS, HistoryManager

    hist_file = tmp_path / "test_hist.json"
    hist = HistoryManager(hist_file)

    for i in range(MAX_HISTORY_TESTS + 50):
        hist.record_test(
            file_path=f"/path/test_{i}.mp4",
            codec="h264",
            original_size=1000,
            estimated_size=500,
            gain_pct=50.0,
            ratio=0.5,
            quality=50,
        )

    data = hist.get_all()
    assert len(data["tests"]) == MAX_HISTORY_TESTS
    assert data["tests"][-1]["name"] == f"test_{MAX_HISTORY_TESTS + 49}.mp4"


def test_supported_extensions_contains_common_formats() -> None:
    for ext in ("mp4", "mkv", "avi", "mov", "m4v"):
        assert ext in SUPPORTED_EXTENSIONS


def test_transcode_nonexistent_file(tmp_path: Path) -> None:
    res = transcode(tmp_path / "nonexistent.mp4", library_root=tmp_path)
    assert res["status"] == "error"
    assert "does not exist" in res["error_message"]


@patch("shutil.disk_usage")
def test_transcode_insufficient_ssd_staging_space(mock_usage: MagicMock, tmp_path: Path) -> None:
    src = tmp_path / "big_movie.mp4"
    src.write_bytes(b"0" * 100_000)

    staging = tmp_path / "ssd_staging"
    staging.mkdir()

    # Free space less than 2x source size (e.g. 50 KB vs 200 KB needed)
    mock_usage.return_value = (100_000, 50_000, 50_000)

    res = transcode(src, library_root=tmp_path, staging_dir=staging)
    assert res["status"] == "error"
    assert "Insufficient disk space" in res["error_message"]


@patch("slim_video.transcoder.get_duration")
@patch("slim_video.transcoder._run_with_progress")
def test_transcode_direct_delete_original(
    mock_run: MagicMock, mock_dur: MagicMock, tmp_path: Path
) -> None:
    import subprocess

    src = tmp_path / "movie_to_delete.mp4"
    src.write_bytes(b"0" * 10_000)
    mock_dur.return_value = 60.0

    def _fake_run(
        cmd: list[str], duration: float = 0.0, callback: Any = None
    ) -> subprocess.CompletedProcess[str]:
        out = Path(cmd[-3])
        out.write_bytes(b"0" * 4_000)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    mock_run.side_effect = _fake_run

    res = transcode(src, library_root=tmp_path, delete_original=True)
    assert res["status"] == "ok"
    assert res["deleted_original"] is True
    assert not src.exists()
    assert Path(res["output_path"]).exists()


@patch("slim_video.transcoder.get_duration")
@patch("slim_video.transcoder._run_with_progress")
def test_transcode_quarantine_move(
    mock_run: MagicMock, mock_dur: MagicMock, tmp_path: Path
) -> None:
    import subprocess

    src = tmp_path / "movie_to_quarantine.mp4"
    src.write_bytes(b"0" * 10_000)
    mock_dur.return_value = 60.0

    def _fake_run(
        cmd: list[str], duration: float = 0.0, callback: Any = None
    ) -> subprocess.CompletedProcess[str]:
        out = Path(cmd[-3])
        out.write_bytes(b"0" * 4_000)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    mock_run.side_effect = _fake_run

    res = transcode(src, library_root=tmp_path, delete_original=False)
    assert res["status"] == "ok"
    assert res["deleted_original"] is False
    assert not src.exists()
    assert Path(res["quarantine_path"]).exists()
    assert Path(res["output_path"]).exists()
