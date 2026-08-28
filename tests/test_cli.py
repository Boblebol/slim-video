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


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "slim-video" in result.output
    assert "Alexandre Enouf" in result.output


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


@patch("slim_video.cli.check_dependencies")
@patch("slim_video.cli.find_h264_candidates")
def test_cli_estimate_command(
    mock_candidates: MagicMock, mock_deps: MagicMock, tmp_path: Path
) -> None:
    mock_deps.return_value = []
    mock_candidates.return_value = ([], [])

    result = runner.invoke(app, ["estimate", str(tmp_path)])
    assert result.exit_code == 0
    assert "No H.264 video files found" in result.output


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

    result_get = runner.invoke(app, ["config", "get", "min_gain_percent"])
    assert result_get.exit_code == 0
    assert "12.5" in result_get.output


def test_cli_history_commands() -> None:
    result_stats = runner.invoke(app, ["history", "stats"])
    assert result_stats.exit_code == 0

    result_clear = runner.invoke(app, ["history", "clear"])
    assert result_clear.exit_code == 0
    assert "cleared successfully" in result_clear.output


def test_cli_doctor_command() -> None:
    result = runner.invoke(app, ["doctor", "--no-benchmark"])
    assert result.exit_code == 0
    assert "Diagnostic Results" in result.output


@patch("slim_video.cli.check_dependencies")
@patch("slim_video.cli.find_h264_candidates")
def test_cli_transcode_delete_original_flag(
    mock_candidates: MagicMock, mock_deps: MagicMock, tmp_path: Path
) -> None:
    mock_deps.return_value = []
    mock_candidates.return_value = ([], [])

    result = runner.invoke(app, ["transcode", str(tmp_path), "--yes", "--delete-original"])
    assert result.exit_code == 0


def test_cli_config_delete_original() -> None:
    result_set = runner.invoke(app, ["config", "set", "delete_original", "true"])
    assert result_set.exit_code == 0
    assert "Updated 'delete_original' to True" in result_set.output

    result_get = runner.invoke(app, ["config", "get", "delete_original"])
    assert result_get.exit_code == 0
    assert "True" in result_get.output


def test_cli_temp_dir_without_ssd_staging_fails(tmp_path: Path) -> None:
    result = runner.invoke(app, ["transcode", str(tmp_path), "--temp-dir", "/tmp/slim-custom"])
    assert result.exit_code == 1
    assert "--temp-dir" in result.output
    assert "--ssd-staging" in result.output


@patch("slim_video.cli.check_dependencies")
@patch("slim_video.cli.find_h264_candidates")
def test_cli_ssd_staging_flags(
    mock_candidates: MagicMock, mock_deps: MagicMock, tmp_path: Path
) -> None:
    mock_deps.return_value = []
    mock_candidates.return_value = ([], [])

    result = runner.invoke(app, ["transcode", str(tmp_path), "--yes", "--ssd-staging"])
    assert result.exit_code == 0


@patch("slim_video.cli.check_dependencies")
@patch("slim_video.cli.find_h264_candidates")
def test_cli_ssd_staging_with_custom_temp_dir(
    mock_candidates: MagicMock, mock_deps: MagicMock, tmp_path: Path
) -> None:
    mock_deps.return_value = []
    mock_candidates.return_value = ([], [])

    custom_dir = str(tmp_path / "custom_temp")
    result = runner.invoke(
        app, ["transcode", str(tmp_path), "--yes", "--ssd-staging", "--temp-dir", custom_dir]
    )
    assert result.exit_code == 0


def test_cli_config_ssd_staging_and_temp_dir() -> None:
    result_set = runner.invoke(app, ["config", "set", "ssd_staging", "true"])
    assert result_set.exit_code == 0
    assert "Updated 'ssd_staging' to True" in result_set.output

    result_get = runner.invoke(app, ["config", "get", "ssd_staging"])
    assert result_get.exit_code == 0
    assert "True" in result_get.output

    result_set2 = runner.invoke(app, ["config", "set", "temp_dir", "/tmp/custom-slim"])
    assert result_set2.exit_code == 0
    assert "Updated 'temp_dir' to /tmp/custom-slim" in result_set2.output

    result_get2 = runner.invoke(app, ["config", "get", "temp_dir"])
    assert result_get2.exit_code == 0
    assert "/tmp/custom-slim" in result_get2.output


@patch("slim_video.cli.check_dependencies")
@patch("slim_video.cli.find_h264_candidates")
def test_cli_json_flags(mock_find: MagicMock, mock_deps: MagicMock, tmp_path: Path) -> None:
    mock_deps.return_value = []
    mock_find.return_value = ([], [])

    # estimate --json
    res_est = runner.invoke(app, ["estimate", str(tmp_path), "--json"])
    assert res_est.exit_code == 0
    assert '"directory"' in res_est.output

    # config show --json
    res_cfg = runner.invoke(app, ["config", "show", "--json"])
    assert res_cfg.exit_code == 0
    assert '"min_gain_percent"' in res_cfg.output

    # doctor --json
    res_doc = runner.invoke(app, ["doctor", "--no-benchmark", "--json"])
    assert res_doc.exit_code == 0
    assert '"name"' in res_doc.output

    # history stats --json
    res_hist = runner.invoke(app, ["history", "stats", "--json"])
    assert res_hist.exit_code == 0
    assert '"stats"' in res_hist.output
