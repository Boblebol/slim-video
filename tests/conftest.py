"""Global pytest fixtures and environment isolation."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest

from slim_video.config import config_manager


@pytest.fixture(autouse=True)
def isolate_test_config_and_history(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[None, None, None]:
    """Isolate configuration and history files during test runs to avoid mutating user home."""
    test_dir = tmp_path_factory.mktemp("test_env")
    test_config_file = test_dir / ".slim_video_config.json"
    test_history_file = test_dir / ".slim_video_history.json"

    original_config_path = config_manager.config_path
    config_manager.config_path = test_config_file

    with (
        patch("slim_video.history.DEFAULT_HISTORY_FILE", test_history_file),
        patch("slim_video.constants.DEFAULT_HISTORY_FILE", test_history_file),
        patch("slim_video.constants.DEFAULT_CONFIG_PATH", test_config_file),
    ):
        try:
            yield
        finally:
            config_manager.config_path = original_config_path
