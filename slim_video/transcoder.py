"""Hardware-accelerated HEVC transcoding engine with quarantine safety."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Callable, Optional

from slim_video.estimator import DEFAULT_QUALITY, _run_with_progress
from slim_video.probing import QUARANTINE_DIR, get_duration
from slim_video.tree_selector import fmt_bytes

logger = logging.getLogger("slim_video.transcoder")

DEFAULT_STAGING_DIR: Path = Path("/tmp/slim-video")


def _cleanup_file(path: Path) -> None:
    """Safely delete a temporary file if it exists."""
    if path.exists():
        try:
            path.unlink()
            logger.debug("Cleaned up temporary file: %s", path)
        except Exception as exc:
            logger.warning("Could not delete temporary file %s: %s", path, exc)


def transcode(
    src: Path,
    library_root: Path,
    quality: int = DEFAULT_QUALITY,
    progress_callback: Optional[Callable[[float, float, str], None]] = None,
    status_callback: Optional[Callable[[str], None]] = None,
    delete_original: bool = False,
    staging_dir: Optional[Path] = None,
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
        status_callback: Status callback for high-level phase updates (space check, moving, cleanup).
        delete_original: If True, delete original file directly instead of moving to quarantine.
        staging_dir: Optional SSD directory where intermediate encoding file is written to avoid
                     head-thrashing on external mechanical HDDs before moving to final destination.

    Returns:
        Dictionary with status ("ok"|"error"), output_path, quarantine_path, output_size, deleted_original.
    """
    if not src.exists():
        err_msg = f"Source file does not exist: {src}"
        logger.error(err_msg)
        return {
            "status": "error",
            "error_message": err_msg,
            "output_path": None,
            "quarantine_path": None,
            "deleted_original": False,
            "output_size": 0,
        }

    orig_size = src.stat().st_size
    duration = get_duration(src)
    final_output = src.with_name(f"{src.stem}.hevc.mkv")

    if staging_dir is not None:
        staging_path = Path(staging_dir)
        staging_path.mkdir(parents=True, exist_ok=True)
        temp_output = staging_path / f".tmp_{src.stem}.hevc.mkv"

        # Check that staging directory has at least 2x original file size of free space
        if status_callback:
            status_callback("Checking staging disk space…")
        try:
            _, _, free_space = shutil.disk_usage(str(staging_path))
            required_space = 2 * orig_size
            logger.info(
                "Staging disk space check for '%s': free=%s, required (2x)=%s",
                staging_path,
                fmt_bytes(free_space),
                fmt_bytes(required_space),
            )
            if free_space < required_space:
                err_msg = (
                    f"Insufficient disk space in staging directory '{staging_path}': "
                    f"requires at least 2x original size ({fmt_bytes(required_space)}), "
                    f"but only {fmt_bytes(free_space)} is available."
                )
                logger.error(err_msg)
                return {
                    "status": "error",
                    "error_message": err_msg,
                    "output_path": None,
                    "quarantine_path": None,
                    "deleted_original": False,
                    "output_size": 0,
                }
        except Exception as exc:
            logger.warning("Could not verify staging disk space on %s: %s", staging_path, exc)
    else:
        temp_output = src.with_name(f".tmp_{src.stem}.hevc.mkv")

    # Ensure any lingering temp file is cleaned up before starting
    _cleanup_file(temp_output)

    try:
        if status_callback:
            status_callback("Encoding (VideoToolbox 10-bit HEVC)…")

        logger.info("Transcoding '%s' -> '%s' (quality=%d)", src, temp_output, quality)

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
            logger.warning(
                "VideoToolbox encoding failed for '%s' (code %d). Trying libx265 fallback...",
                src,
                result.returncode,
            )
            if status_callback:
                status_callback("Hardware failed, falling back to libx265 CPU…")

            _cleanup_file(temp_output)

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
            _cleanup_file(temp_output)
            err_msg = result.stderr.strip() or "FFmpeg encoding failed"
            logger.error("Encoding failed for '%s': %s", src, err_msg)
            return {
                "status": "error",
                "error_message": err_msg,
                "output_path": None,
                "quarantine_path": None,
                "deleted_original": False,
                "output_size": 0,
            }

        # Move / Transfer temp output to final destination
        if status_callback:
            if staging_dir is not None:
                status_callback("📦 Transferring final video to external disk…")
            else:
                status_callback("Finalizing output file…")

        logger.info("Moving '%s' -> '%s'", temp_output, final_output)
        if final_output.exists():
            final_output.unlink()
        shutil.move(str(temp_output), str(final_output))

        # Validate that the final destination file exists and is non-empty
        if not final_output.exists() or final_output.stat().st_size == 0:
            err_msg = f"Final output verification failed: '{final_output}' is missing or empty."
            logger.error(err_msg)
            return {
                "status": "error",
                "error_message": err_msg,
                "output_path": None,
                "quarantine_path": None,
                "deleted_original": False,
                "output_size": 0,
            }

        # Handle original file (quarantine or delete) ONLY after verified transfer
        quarantine_dest: Optional[str] = None
        if delete_original:
            if status_callback:
                status_callback("🗑️ Deleting original file…")
            if src.exists():
                src.unlink()
                logger.info("Deleted original file after verified transfer: %s", src)
        else:
            if status_callback:
                status_callback("Quarantining original file…")
            # Move original to quarantine directory preserving relative path
            quarantine_root = library_root / QUARANTINE_DIR
            try:
                relative = src.relative_to(library_root)
            except ValueError:
                relative = Path(src.name)

            q_path = quarantine_root / relative
            q_path.parent.mkdir(parents=True, exist_ok=True)
            if q_path.exists():
                q_path.unlink()
            shutil.move(str(src), str(q_path))
            quarantine_dest = str(q_path)
            logger.info("Moved original to quarantine: %s", q_path)

        return {
            "status": "ok",
            "output_path": str(final_output),
            "quarantine_path": quarantine_dest,
            "deleted_original": delete_original,
            "output_size": final_output.stat().st_size,
        }

    finally:
        # Guarantee that no intermediate temp file remains in staging or source dir
        _cleanup_file(temp_output)
