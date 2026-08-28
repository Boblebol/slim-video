"""Unit tests for slim_video.ui.prompts module."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from slim_video.config import ConfigManager
from slim_video.ui.prompts import prompt_interactive_folder_selection, run_config_wizard


@patch("slim_video.ui.prompts.inquirer.select")
def test_prompt_folder_current_dir(mock_select: MagicMock) -> None:
    mock_select.return_value.execute.return_value = f"📁 Current Directory ({os.getcwd()})"
    res = prompt_interactive_folder_selection()
    assert res == os.getcwd()


@patch("slim_video.ui.prompts.inquirer.text")
@patch("slim_video.ui.prompts.inquirer.select")
def test_prompt_folder_custom_dir(mock_select: MagicMock, mock_text: MagicMock) -> None:
    mock_select.return_value.execute.return_value = "🔍 Enter Custom Directory Path…"
    mock_text.return_value.execute.return_value = "/Volumes/Custom/Path"
    res = prompt_interactive_folder_selection()
    assert res == "/Volumes/Custom/Path"


@patch("slim_video.ui.prompts.inquirer.select")
def test_prompt_folder_movies(mock_select: MagicMock) -> None:
    movies_path = str(Path.home() / "Movies")
    mock_select.return_value.execute.return_value = f"🏠 Movies Folder ({movies_path})"
    res = prompt_interactive_folder_selection()
    assert res == movies_path


@patch("slim_video.ui.prompts.inquirer.text")
@patch("slim_video.ui.prompts.inquirer.select")
def test_prompt_folder_estimate_callback(mock_select: MagicMock, mock_text: MagicMock) -> None:
    mock_select.return_value.execute.return_value = "📊 Estimate Potential Space Savings (Dry Run)"
    mock_text.return_value.execute.return_value = "/Volumes/ToEstimate"

    on_estimate = MagicMock()
    with pytest.raises(SystemExit):
        prompt_interactive_folder_selection(on_estimate=on_estimate)
    on_estimate.assert_called_once_with("/Volumes/ToEstimate")


@patch("slim_video.ui.prompts.inquirer.select")
def test_prompt_folder_doctor_callback(mock_select: MagicMock) -> None:
    mock_select.return_value.execute.return_value = "🩺 Run Hardware & System Diagnostics (Doctor)"
    on_doctor = MagicMock()
    with pytest.raises(SystemExit):
        prompt_interactive_folder_selection(on_doctor=on_doctor)
    on_doctor.assert_called_once()


@patch("slim_video.ui.prompts.inquirer.select")
def test_prompt_folder_config_callback(mock_select: MagicMock) -> None:
    mock_select.return_value.execute.return_value = "⚙️  Open Configuration Settings"
    on_config = MagicMock()
    with pytest.raises(SystemExit):
        prompt_interactive_folder_selection(on_config=on_config)
    on_config.assert_called_once()


@patch("slim_video.ui.prompts.inquirer.select")
def test_prompt_folder_history_callback(mock_select: MagicMock) -> None:
    mock_select.return_value.execute.return_value = "📈 View Lifetime Savings History"
    on_history = MagicMock()
    with pytest.raises(SystemExit):
        prompt_interactive_folder_selection(on_history=on_history)
    on_history.assert_called_once()


@patch("slim_video.ui.prompts.inquirer.select")
def test_prompt_folder_exit(mock_select: MagicMock) -> None:
    mock_select.return_value.execute.return_value = "🚪 Exit"
    with pytest.raises(SystemExit):
        prompt_interactive_folder_selection()


@patch("slim_video.ui.prompts.inquirer.confirm")
@patch("slim_video.ui.prompts.inquirer.text")
def test_run_config_wizard(mock_text: MagicMock, mock_confirm: MagicMock, tmp_path: Path) -> None:
    cfg_path = tmp_path / "test_config.json"
    mgr = ConfigManager(config_path=cfg_path)

    mock_text.return_value.execute.side_effect = [
        "15.0",  # min_gain_percent
        "25",  # sample_duration_seconds
        "45",  # quality
        "_quarantine_test",  # quarantine_dir
        "/tmp/custom_ssd",  # temp_dir
    ]
    mock_confirm.return_value.execute.side_effect = [
        True,  # auto_sample_test
        True,  # delete_original
        True,  # ssd_staging
    ]

    run_config_wizard(mgr)
    loaded = mgr.load()
    assert loaded.min_gain_percent == 15.0
    assert loaded.sample_duration_seconds == 25
    assert loaded.quality == 45
    assert loaded.delete_original is True
    assert loaded.ssd_staging is True
    assert loaded.temp_dir == "/tmp/custom_ssd"
