"""Unit tests for slim_video.workflow module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from slim_video.models import FileItem
from slim_video.workflow import display_estimation_table, execute_batch, run_main_workflow


def test_display_estimation_table(tmp_path: Path) -> None:
    items = [
        FileItem(
            path=tmp_path / "vid1.mp4",
            rel_path=Path("vid1.mp4"),
            size=1000,
            codec="h264",
            resolution="1920x1080",
            fps=30.0,
            duration=10.0,
            audio="aac",
            selected=True,
            estimated_size=500,
            estimated_gain_pct=50.0,
        ),
        FileItem(
            path=tmp_path / "vid2.mp4",
            rel_path=Path("vid2.mp4"),
            size=1000,
            codec="h264",
            resolution="1920x1080",
            fps=30.0,
            duration=10.0,
            audio="aac",
            selected=False,
            estimated_size=950,
            estimated_gain_pct=5.0,
        ),
    ]
    # Should execute without errors
    display_estimation_table(tmp_path, items, min_gain=10.0)


@patch("slim_video.workflow.transcode")
def test_execute_batch(mock_transcode: MagicMock, tmp_path: Path) -> None:
    mock_transcode.return_value = {
        "status": "ok",
        "output_size": 400,
        "output_path": str(tmp_path / "vid1.hevc.mkv"),
        "quarantine_path": str(tmp_path / "_originals_to_delete" / "vid1.mp4"),
        "deleted_original": False,
    }

    items = [
        FileItem(
            path=tmp_path / "vid1.mp4",
            rel_path=Path("vid1.mp4"),
            size=1000,
            codec="h264",
            resolution="1920x1080",
            fps=30.0,
            duration=10.0,
            audio="aac",
            selected=True,
            estimated_size=400,
            estimated_gain_pct=60.0,
        )
    ]

    summary = execute_batch(
        root=tmp_path,
        items=items,
        total_scanned=1,
        quality=50,
        delete_original=False,
    )

    assert summary.total_files_successful == 1
    assert summary.total_saved_bytes == 600
    assert summary.total_gain_pct == 60.0


@patch("slim_video.workflow.find_h264_candidates")
def test_run_main_workflow_empty_dir(mock_find: MagicMock, tmp_path: Path) -> None:
    mock_find.return_value = ([], [])
    run_main_workflow(path_arg=str(tmp_path), yes=True)


@patch("slim_video.workflow.find_h264_candidates")
def test_run_main_workflow_already_hevc(mock_find: MagicMock, tmp_path: Path) -> None:
    mock_find.return_value = ([], [tmp_path / "movie.hevc.mkv"])
    run_main_workflow(path_arg=str(tmp_path), yes=True)


@patch("slim_video.workflow.find_h264_candidates")
@patch("slim_video.workflow.estimate_savings")
@patch("slim_video.workflow.get_video_codec")
@patch("slim_video.workflow.get_duration")
@patch("slim_video.workflow.get_resolution")
@patch("slim_video.workflow.get_fps")
@patch("slim_video.workflow.get_audio_summary")
def test_run_main_workflow_dry_run_with_candidates(
    mock_audio: MagicMock,
    mock_fps: MagicMock,
    mock_res: MagicMock,
    mock_dur: MagicMock,
    mock_codec: MagicMock,
    mock_est: MagicMock,
    mock_find: MagicMock,
    tmp_path: Path,
) -> None:
    v1 = tmp_path / "vid1.mp4"
    v2 = tmp_path / "vid2.mp4"
    v1.write_bytes(b"0" * 1000)
    v2.write_bytes(b"0" * 1000)

    mock_find.return_value = ([v1, v2], [])
    mock_codec.return_value = "h264"
    mock_dur.return_value = 100.0
    mock_res.return_value = "1920x1080"
    mock_fps.return_value = 24.0
    mock_audio.return_value = "AAC"

    # v1 is good gain (50%), v2 is low gain (5%)
    mock_est.side_effect = [
        {
            "original_size": 1000,
            "estimated_size": 500,
            "gain_pct": 50.0,
            "ratio": 0.5,
        },
        {
            "original_size": 1000,
            "estimated_size": 950,
            "gain_pct": 5.0,
            "ratio": 0.95,
        },
    ]

    run_main_workflow(path_arg=str(tmp_path), min_gain=10.0, dry_run=True, yes=True)


@patch("slim_video.workflow.find_h264_candidates")
@patch("slim_video.workflow.estimate_savings")
@patch("slim_video.workflow.get_video_codec")
@patch("slim_video.workflow.get_duration")
@patch("slim_video.workflow.get_resolution")
@patch("slim_video.workflow.get_fps")
@patch("slim_video.workflow.get_audio_summary")
@patch("slim_video.workflow.select_files_interactive")
@patch("slim_video.workflow.execute_batch")
def test_run_main_workflow_full_batch_run(
    mock_batch: MagicMock,
    mock_select: MagicMock,
    mock_audio: MagicMock,
    mock_fps: MagicMock,
    mock_res: MagicMock,
    mock_dur: MagicMock,
    mock_codec: MagicMock,
    mock_est: MagicMock,
    mock_find: MagicMock,
    tmp_path: Path,
) -> None:
    v1 = tmp_path / "vid1.mp4"
    v1.write_bytes(b"0" * 1000)

    mock_find.return_value = ([v1], [])
    mock_codec.return_value = "h264"
    mock_dur.return_value = 100.0
    mock_res.return_value = "1920x1080"
    mock_fps.return_value = 24.0
    mock_audio.return_value = "AAC"
    mock_est.return_value = {
        "original_size": 1000,
        "estimated_size": 500,
        "gain_pct": 50.0,
        "ratio": 0.5,
    }

    item = FileItem(
        path=v1,
        rel_path=Path("vid1.mp4"),
        size=1000,
        codec="h264",
        resolution="1920x1080",
        fps=24.0,
        duration=100.0,
        audio="AAC",
        selected=True,
    )
    mock_select.return_value = [item]

    run_main_workflow(path_arg=str(tmp_path), yes=True)
    mock_batch.assert_called_once()
