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

    # Verify original was deleted, not quarantined
    assert not src.exists()
    quarantine_dir = tmp_path / "_originals_to_delete"
    assert not quarantine_dir.exists()


def test_supported_extensions_contains_common_formats() -> None:
    for ext in ("mp4", "mkv", "avi", "mov", "m4v"):
        assert ext in SUPPORTED_EXTENSIONS
