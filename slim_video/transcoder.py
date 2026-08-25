"""Hardware-accelerated HEVC transcoding engine with quarantine safety."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Callable, Optional

from slim_video.estimator import DEFAULT_QUALITY, _run_with_progress
from slim_video.probing import QUARANTINE_DIR, get_duration


def transcode(
    src: Path,
    library_root: Path,
    quality: int = DEFAULT_QUALITY,
    progress_callback: Optional[Callable[[float, float, str], None]] = None,
    delete_original: bool = False,
) -> dict[str, Any]:
    """Transcode *src* (H.264) to HEVC / x265 with optimal automated settings.

    Settings automatically preserve:
    - Same perceived visual quality using 10-bit HEVC (p010le) + spatial AQ
    - All audio streams without re-encoding (-c:a copy)
    - All subtitle streams (-c:s copy)
    - All chapters and metadata (-map_metadata 0 -map_chapters 0)
    - Maximum Apple & media player compatibility (-tag:v hvc1)

    On success, the original file is either permanently deleted (if delete_original=True)
    or moved into the quarantine folder ``_originals_to_delete``.

    Args:
        src: Path to source video file.
        library_root: Base folder being processed.
        quality: VideoToolbox quality (default 50).
        progress_callback: Progress callback (pct, elapsed, speed).
        delete_original: If True, delete original file directly instead of moving to quarantine.

    Returns:
        Dictionary with status ("ok"|"error"), output_path, quarantine_path, output_size, deleted_original.
    """
    final_output = src.with_name(f"{src.stem}.hevc.mkv")
    temp_output = src.with_name(f".tmp_{src.stem}.hevc.mkv")
    duration = get_duration(src)

    # Ensure any lingering temp file is cleaned up
    if temp_output.exists():
        try:
            temp_output.unlink()
        except Exception:
            pass

    # Command using VideoToolbox hardware acceleration
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-map",
        "0",  # Keep all video, audio, and subtitle streams
        "-map_metadata",
        "0",  # Preserve global & stream metadata
        "-map_chapters",
        "0",  # Preserve chapter marks
        "-c:v",
        "hevc_videotoolbox",  # Hardware-accelerated HEVC on Apple Silicon
        "-q:v",
        str(quality),  # VideoToolbox quality factor (50 = optimal sweetspot)
        "-tag:v",
        "hvc1",  # QuickTime / Apple / Plex compatibility
        "-pix_fmt",
        "p010le",  # 10-bit color for artifact-free gradients & better compression
        "-spatial_aq",
        "1",  # Spatial adaptive quantization to preserve fine texture
        "-allow_sw",
        "0",  # Force hardware encoding
        "-c:a",
        "copy",  # Lossless copy of all audio tracks
        "-c:s",
        "copy",  # Lossless copy of all subtitle tracks
        str(temp_output),
        "-loglevel",
        "error",
    ]

    result = _run_with_progress(cmd, duration=duration, callback=progress_callback)

    # If VideoToolbox hardware encoding failed, attempt libx265 fallback
    if result.returncode != 0 or not temp_output.exists() or temp_output.stat().st_size == 0:
        if temp_output.exists():
            temp_output.unlink()

        cmd_fallback = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-map",
            "0",
            "-map_metadata",
            "0",
            "-map_chapters",
            "0",
            "-c:v",
            "libx265",
            "-crf",
            "22",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p10le",
            "-tag:v",
            "hvc1",
            "-c:a",
            "copy",
            "-c:s",
            "copy",
            str(temp_output),
            "-loglevel",
            "error",
        ]
        result = _run_with_progress(cmd_fallback, duration=duration, callback=progress_callback)

    # Check if encoding produced a valid non-empty file
    if result.returncode != 0 or not temp_output.exists() or temp_output.stat().st_size == 0:
        if temp_output.exists():
            temp_output.unlink()
        return {
            "status": "error",
            "error_message": result.stderr.strip() or "FFmpeg encoding failed",
            "output_path": None,
            "quarantine_path": None,
            "deleted_original": False,
            "output_size": 0,
        }

    # Move temp output to final destination
    if final_output.exists():
        final_output.unlink()
    shutil.move(str(temp_output), str(final_output))

    quarantine_dest: Optional[str] = None
    if delete_original:
        if src.exists():
            src.unlink()
    else:
        # Move original to quarantine directory preserving relative path
        quarantine_root = library_root / QUARANTINE_DIR
        try:
            relative = src.relative_to(library_root)
        except ValueError:
            relative = Path(src.name)

        q_path = quarantine_root / relative
        q_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(q_path))
        quarantine_dest = str(q_path)

    return {
        "status": "ok",
        "output_path": str(final_output),
        "quarantine_path": quarantine_dest,
        "deleted_original": delete_original,
        "output_size": final_output.stat().st_size,
    }
