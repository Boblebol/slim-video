"""Shared constants, defaults, and definitions for slim-video."""

from __future__ import annotations

from pathlib import Path

#: Default VideoToolbox HEVC quality factor (1=best, 100=smallest)
DEFAULT_QUALITY: int = 50

#: Default duration in seconds of test encode samples
SAMPLE_SECONDS: int = 20

#: Default SSD staging directory for fast local transcode intermediate files
DEFAULT_STAGING_DIR: Path = Path("/tmp/slim-video")

#: Quarantine folder name where originals are moved after successful transcoding
QUARANTINE_DIR: str = "_originals_to_delete"

#: Default user configuration file location
DEFAULT_CONFIG_PATH: Path = Path.home() / ".slim_video_config.json"

#: Default transcode and test history file location
DEFAULT_HISTORY_FILE: Path = Path.home() / ".slim_video_history.json"

#: Video container extensions scanned recursively
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {"mp4", "mkv", "avi", "mov", "m4v", "wmv", "flv", "ts", "webm"}
)

#: Codec identifiers that represent H.264 / AVC
H264_CODECS: frozenset[str] = frozenset({"h264", "avc", "avc1", "x264"})

#: Codec identifiers that represent HEVC / H.265
HEVC_CODECS: frozenset[str] = frozenset({"hevc", "h265", "hvc1", "x265"})
