"""slim-video — Smart Apple Silicon batch video transcoder with tree selection & sample estimation."""

__version__ = "1.5.0"
__author__ = "Alexandre Enouf"
__email__ = "alexandre.enouf@gmail.com"
__url__ = "https://alexandre-enouf.fr"
__github__ = "https://github.com/Boblebol/slim-video"
__license__ = "MIT"

from slim_video.core import (
    DEFAULT_QUALITY,
    DEFAULT_STAGING_DIR,
    SAMPLE_SECONDS,
    SUPPORTED_EXTENSIONS,
    estimate_savings,
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
from slim_video.models import BatchSummary, FileItem, TranscodeRecord, TreeNode

__all__ = [
    "DEFAULT_QUALITY",
    "DEFAULT_STAGING_DIR",
    "SAMPLE_SECONDS",
    "SUPPORTED_EXTENSIONS",
    "BatchSummary",
    "FileItem",
    "TranscodeRecord",
    "TreeNode",
    "estimate_savings",
    "find_h264_candidates",
    "find_video_files",
    "get_audio_summary",
    "get_duration",
    "get_fps",
    "get_resolution",
    "get_video_codec",
    "is_h264_codec",
    "is_hevc_codec",
    "transcode",
]
