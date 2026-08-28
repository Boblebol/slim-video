"""Unit tests for slim_video.probing module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from slim_video.probing import (
    find_h264_candidates,
    get_audio_summary,
    get_duration,
    get_fps,
    get_resolution,
    get_video_codec,
)


@patch("slim_video.probing._run")
def test_probing_fields_success(mock_run: MagicMock, tmp_path: Path) -> None:
    vid = tmp_path / "sample.mkv"
    mock_run.return_value.stdout = "h264\n"
    assert get_video_codec(vid) == "h264"

    mock_run.return_value.stdout = "120.5\n"
    assert get_duration(vid) == 120.5

    mock_run.return_value.stdout = "1920\n"
    assert "1920" in get_resolution(vid)

    mock_run.return_value.stdout = "24/1\n"
    assert get_fps(vid) == 24.0

    mock_run.return_value.stdout = "aac\n"
    assert "AAC" in get_audio_summary(vid)


@patch("slim_video.probing._run")
def test_probing_fields_empty(mock_run: MagicMock, tmp_path: Path) -> None:
    vid = tmp_path / "empty.mp4"
    mock_run.return_value.stdout = ""

    assert get_video_codec(vid) is None
    assert get_duration(vid) == 0.0
    assert get_resolution(vid) == "Unknown"
    assert get_fps(vid) == 0.0
    assert get_audio_summary(vid) == "No audio"


@patch("slim_video.probing.get_video_codec")
def test_find_h264_candidates(mock_codec: MagicMock, tmp_path: Path) -> None:
    v1 = tmp_path / "video1.mp4"
    v2 = tmp_path / "video2.mkv"
    v3 = tmp_path / "video3.hevc.mkv"
    txt = tmp_path / "subtitles.srt"

    for f in (v1, v2, v3, txt):
        f.touch()

    def _codec_side_effect(path: Path) -> str | None:
        if path == v1:
            return "h264"
        elif path == v2:
            return "mpeg4"
        elif path == v3:
            return "hevc"
        return None

    mock_codec.side_effect = _codec_side_effect

    # By default, only H.264 is candidate
    candidates, already_hevc = find_h264_candidates(tmp_path, all_codecs=False)
    assert v1 in candidates
    assert v2 not in candidates
    assert v3 in already_hevc

    # With all_codecs=True, mpeg4 is also candidate
    candidates_all, _ = find_h264_candidates(tmp_path, all_codecs=True)
    assert v1 in candidates_all
    assert v2 in candidates_all
