"""Media metadata extraction and file discovery using ffprobe."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable, Optional

#: Video container extensions scanned recursively.
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {"mp4", "mkv", "avi", "mov", "m4v", "wmv", "flv", "ts", "webm"}
)

#: Codec identifiers that represent H.264 / AVC.
H264_CODECS: frozenset[str] = frozenset({"h264", "avc", "avc1", "x264"})

#: Codec identifiers that represent HEVC / H.265.
HEVC_CODECS: frozenset[str] = frozenset({"hevc", "h265", "hvc1", "x265"})

#: Quarantine folder name for original files after successful transcoding.
QUARANTINE_DIR: str = "_originals_to_delete"


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and capture stdout/stderr."""
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _ffprobe_field(path: Path, stream_selector: str, entry: str) -> Optional[str]:
    """Extract a single field from ffprobe output."""
    result = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            stream_selector,
            "-show_entries",
            entry,
            "-of",
            "csv=p=0",
            str(path),
        ]
    )
    value = result.stdout.strip().split("\n")[0].strip()
    return value if value and value != "N/A" else None


def is_h264_codec(codec: Optional[str]) -> bool:
    """Return True if codec string corresponds to H.264 / AVC."""
    if not codec:
        return False
    return codec.lower().strip() in H264_CODECS


def is_hevc_codec(codec: Optional[str]) -> bool:
    """Return True if codec string corresponds to HEVC / H.265."""
    if not codec:
        return False
    return codec.lower().strip() in HEVC_CODECS


def get_video_codec(path: Path) -> Optional[str]:
    """Return the video codec name (e.g. ``"h264"``, ``"hevc"``)."""
    return _ffprobe_field(path, "v:0", "stream=codec_name")


def get_duration(path: Path) -> float:
    """Return the video duration in seconds, or 0.0 if unavailable."""
    value = _ffprobe_field(path, "v:0", "format=duration")
    if not value:
        value = _ffprobe_field(path, "v:0", "stream=duration")
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def get_resolution(path: Path) -> str:
    """Return the video resolution as ``"WxH"`` (e.g. ``"1920x1080"``)."""
    width = _ffprobe_field(path, "v:0", "stream=width")
    height = _ffprobe_field(path, "v:0", "stream=height")
    return f"{width}x{height}" if width and height else "Unknown"


def get_fps(path: Path) -> float:
    """Return the video frame rate in FPS, or 0.0 if unavailable."""
    raw = _ffprobe_field(path, "v:0", "stream=r_frame_rate")
    if raw and "/" in raw:
        try:
            num, den = map(float, raw.split("/"))
            return round(num / den, 3) if den else 0.0
        except ValueError:
            pass
    return 0.0


def get_audio_summary(path: Path) -> str:
    """Return a compact audio description (e.g. ``"AAC 2ch"``, ``"AC3 6ch"``)."""
    codec = _ffprobe_field(path, "a:0", "stream=codec_name")
    if not codec:
        return "No audio"
    channels = _ffprobe_field(path, "a:0", "stream=channels")
    ch = f"{channels}ch" if channels else ""
    return f"{codec.upper()} {ch}".strip()


def get_audio_bitrate(path: Path) -> int:
    """Return the audio bitrate in bits per second (default: 160 000)."""
    value = _ffprobe_field(path, "a:0", "stream=bit_rate")
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 160_000


def get_video_metadata(path: Path) -> dict[str, Any]:
    """Extract complete video metadata dictionary in one call."""
    codec = get_video_codec(path) or "unknown"
    duration = get_duration(path)
    resolution = get_resolution(path)
    fps = get_fps(path)
    audio = get_audio_summary(path)
    size = path.stat().st_size if path.exists() else 0

    return {
        "codec": codec,
        "duration": duration,
        "resolution": resolution,
        "fps": fps,
        "audio": audio,
        "size": size,
        "is_h264": is_h264_codec(codec),
        "is_hevc": is_hevc_codec(codec),
    }


def find_video_files(root: Path) -> list[Path]:
    """Recursively find all supported video files under *root*.

    Files inside quarantine directories and hidden directories are excluded.
    """
    if root.is_file():
        return [root] if root.suffix.lower().lstrip(".") in SUPPORTED_EXTENSIONS else []

    files: list[Path] = []
    try:
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if QUARANTINE_DIR in p.parts or any(part.startswith(".") for part in p.parts):
                continue
            if p.suffix.lower().lstrip(".") in SUPPORTED_EXTENSIONS:
                files.append(p)
    except Exception:
        pass
    return sorted(files)


def find_h264_candidates(
    root: Path,
    all_codecs: bool = False,
    progress_callback: Optional[Callable[[Path, int, int], None]] = None,
) -> tuple[list[Path], list[Path]]:
    """Scan directory and partition files into candidates and already-HEVC files."""
    all_videos = find_video_files(root)
    candidates: list[Path] = []
    already_hevc: list[Path] = []

    for f in all_videos:
        codec = get_video_codec(f)
        if is_hevc_codec(codec):
            already_hevc.append(f)
        elif all_codecs or is_h264_codec(codec) or codec is None:
            candidates.append(f)

        if progress_callback:
            progress_callback(f, len(candidates), len(already_hevc))

    return candidates, already_hevc
