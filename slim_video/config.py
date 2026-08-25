"""Configuration manager using Pydantic v2 for slim-video.

Manages persistent user settings stored in ~/.slim_video_config.json.
Settings can be queried and modified via the CLI (`slim-video config`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

DEFAULT_CONFIG_PATH: Path = Path.home() / ".slim_video_config.json"


class AppConfig(BaseModel):
    """Application configuration options with Pydantic v2 validation."""

    min_gain_percent: float = Field(
        default=10.0,
        description="Minimum extrapolated gain % to select by default (< threshold = unchecked)",
    )
    sample_duration_seconds: int = Field(
        default=20,
        description="Duration of test encode sample taken from the middle (seconds)",
    )
    quality: int = Field(
        default=50,
        description="VideoToolbox HEVC quality factor (1=best, 100=smallest)",
    )
    auto_sample_test: bool = Field(
        default=True,
        description="Whether to run automatic 20s sample tests on candidates",
    )
    quarantine_dir: str = Field(
        default="_originals_to_delete",
        description="Subdirectory name where originals are moved after transcoding",
    )
    delete_original: bool = Field(
        default=False,
        description="Whether to permanently delete original files immediately after successful transcode instead of quarantine",
    )
    all_codecs: bool = Field(
        default=False,
        description="Whether to process all non-HEVC video formats or only H.264",
    )
    encoder: str = Field(
        default="hevc_videotoolbox",
        description="FFmpeg HEVC video encoder (default: hevc_videotoolbox)",
    )
    ssd_staging: bool = Field(
        default=False,
        description="Whether to use SSD staging folder to eliminate head-thrashing on external mechanical HDDs",
    )
    temp_dir: str = Field(
        default="/tmp/slim-video",
        description="Custom temporary working directory when SSD staging is enabled",
    )


class ConfigManager:
    """Manages reading, validating, and writing persistent configuration."""

    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH) -> None:
        self.config_path: Path = config_path

    def load(self) -> AppConfig:
        """Load configuration from disk, creating default if missing."""
        if not self.config_path.exists():
            config = AppConfig()
            self.save(config)
            return config

        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return AppConfig.model_validate(data)
        except Exception:
            # Fallback to default if file is corrupted
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        """Save configuration to disk as formatted JSON."""
        try:
            with self.config_path.open("w", encoding="utf-8") as f:
                json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
        except Exception as exc:
            print(f"[config] Warning: Could not save configuration: {exc}")

    def get(self, key: str) -> Any:
        """Get a single setting value."""
        config = self.load()
        if not hasattr(config, key):
            raise KeyError(f"Unknown configuration key: '{key}'")
        return getattr(config, key)

    def set(self, key: str, value_str: str) -> tuple[str, Any]:
        """Set a single setting value with automatic type conversion and validation."""
        config = self.load()
        if not hasattr(config, key):
            raise KeyError(f"Unknown configuration key: '{key}'")

        current_val = getattr(config, key)
        # Type casting
        converted: Any
        if isinstance(current_val, bool):
            converted = value_str.lower() in ("true", "1", "yes", "y", "oui")
        elif isinstance(current_val, int):
            converted = int(value_str)
        elif isinstance(current_val, float):
            converted = float(value_str)
        else:
            converted = str(value_str)

        # Validate with Pydantic
        dumped = config.model_dump()
        dumped[key] = converted
        validated = AppConfig.model_validate(dumped)

        self.save(validated)
        return key, converted

    def reset(self) -> AppConfig:
        """Reset configuration to default values."""
        default_config = AppConfig()
        self.save(default_config)
        return default_config


config_manager = ConfigManager()
