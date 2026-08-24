"""Unit tests for slim_video.cli entrypoints."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from slim_video.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "H.264" in result.output or "transcoder" in result.output


@patch("slim_video.cli.check_dependencies")
def test_cli_missing_dependencies(mock_deps: MagicMock) -> None:
    mock_deps.return_value = ["ffmpeg"]
    result = runner.invoke(app, ["transcode"])
    assert result.exit_code == 1
    assert "Missing required dependencies" in result.output


@patch("slim_video.cli.check_dependencies")
@patch("slim_video.cli.find_h264_candidates")
def test_cli_empty_directory(
    mock_candidates: MagicMock, mock_deps: MagicMock, tmp_path: Path
) -> None:
    mock_deps.return_value = []
    mock_candidates.return_value = ([], [])

    result = runner.invoke(app, ["transcode", str(tmp_path), "--yes"])
    assert result.exit_code == 0
    assert "No H.264 video files found" in result.output


@patch("slim_video.cli.check_dependencies")
@patch("slim_video.cli.find_h264_candidates")
def test_cli_all_already_hevc(
    mock_candidates: MagicMock, mock_deps: MagicMock, tmp_path: Path
) -> None:
    mock_deps.return_value = []
    mock_candidates.return_value = ([], [tmp_path / "video.hevc.mkv"])

    result = runner.invoke(app, ["transcode", str(tmp_path), "--yes"])
    assert result.exit_code == 0
    assert "already optimized in HEVC" in result.output


def test_cli_config_commands() -> None:
    result_show = runner.invoke(app, ["config", "show"])
    assert result_show.exit_code == 0
    assert "min_gain_percent" in result_show.output

    result_path = runner.invoke(app, ["config", "path"])
    assert result_path.exit_code == 0
    assert ".slim_video_config.json" in result_path.output

    result_set = runner.invoke(app, ["config", "set", "min_gain_percent", "12.5"])
    assert result_set.exit_code == 0
    assert "Updated 'min_gain_percent' to 12.5" in result_set.output


def test_cli_doctor_command() -> None:
    result = runner.invoke(app, ["doctor", "--no-benchmark"])
    assert result.exit_code == 0
    assert "Diagnostic Results" in result.output
