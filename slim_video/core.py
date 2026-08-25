"""Core interface re-exporting probing, estimation, and transcoding engines."""

from __future__ import annotations

import shutil

from slim_video.estimator import DEFAULT_QUALITY, SAMPLE_SECONDS, estimate_savings
from slim_video.probing import (
    H264_CODECS,
    HEVC_CODECS,
    QUARANTINE_DIR,
    SUPPORTED_EXTENSIONS,
    find_h264_candidates,
    find_video_files,
    get_audio_bitrate,
    get_audio_summary,
    get_duration,
    get_fps,
    get_resolution,
    get_video_codec,
    get_video_metadata,
    is_h264_codec,
    is_hevc_codec,
)
from slim_video.transcoder import DEFAULT_STAGING_DIR, transcode


def check_dependencies() -> list[str]:
    """Return a list of missing required system binaries."""
    return [binary for binary in ("ffmpeg", "ffprobe") if not shutil.which(binary)]


__all__ = [
    "DEFAULT_QUALITY",
    "DEFAULT_STAGING_DIR",
    "H264_CODECS",
    "HEVC_CODECS",
    "QUARANTINE_DIR",
    "SAMPLE_SECONDS",
    "SUPPORTED_EXTENSIONS",
    "check_dependencies",
    "estimate_savings",
    "find_h264_candidates",
    "find_video_files",
    "get_audio_bitrate",
    "get_audio_summary",
    "get_duration",
    "get_fps",
    "get_resolution",
    "get_video_codec",
    "get_video_metadata",
    "is_h264_codec",
    "is_hevc_codec",
    "transcode",
]
