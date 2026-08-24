"""Real sample-based space estimation engine using Apple VideoToolbox."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional

from hevc_cli.probing import _run, get_audio_bitrate, get_duration

SAMPLE_SECONDS: int = 20
DEFAULT_QUALITY: int = 50


def _run_with_progress(
    cmd: list[str],
    duration: float = 0.0,
    callback: Optional[Callable[[float, float, str], None]] = None,
) -> subprocess.CompletedProcess[str]:
    """Run ffmpeg and emit real-time progress via callback."""
    if not callback or duration <= 0:
        return _run(cmd)

    progress_cmd = list(cmd) + ["-progress", "pipe:1", "-nostats"]
    proc = subprocess.Popen(
        progress_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    speed = "1.0x"
    elapsed = 0.0

    if proc.stdout:
        for line in proc.stdout:
            line = line.strip()
            if line.startswith("out_time_us="):
                try:
                    elapsed = float(line.split("=")[1]) / 1_000_000
                    pct = min(100.0, max(0.0, (elapsed / duration) * 100))
                    callback(pct, elapsed, speed)
                except (ValueError, ZeroDivisionError):
                    pass
            elif line.startswith("speed="):
                raw = line.split("=")[1].strip()
                if raw and raw != "N/A":
                    speed = raw

    proc.wait()
    stderr = proc.stderr.read() if proc.stderr else ""
    return subprocess.CompletedProcess(progress_cmd, proc.returncode, "", stderr)


def estimate_savings(
    path: Path,
    quality: int = DEFAULT_QUALITY,
    sample_seconds: int = SAMPLE_SECONDS,
    callback: Optional[Callable[[float, float, str], None]] = None,
) -> dict[str, Any]:
    """Estimate HEVC space savings for *path* by encoding a real sample.

    Extracts a sample from the exact middle of the file and encodes it on /tmp.
    Extrapolates total file savings based on video stream compression ratio.

    Args:
        path: Source video file.
        quality: VideoToolbox quality factor (1–100).
        sample_seconds: Duration of the test sample in seconds (default: 20s).
        callback: Optional progress callback ``(pct, elapsed_sec, speed)``.

    Returns:
        Dictionary with original_size, estimated_size, gain_pct, ratio.
    """
    duration = get_duration(path)
    original_size = path.stat().st_size if path.exists() else 0
    if original_size == 0:
        return {"error": "file_empty_or_missing"}

    audio_bitrate = get_audio_bitrate(path)
    audio_bytes = (audio_bitrate * duration) / 8
    video_bytes = max(original_size - audio_bytes, 1)

    sample_duration = min(sample_seconds, duration) if duration > 0 else sample_seconds
    start = (
        max(0.0, (duration / 2) - (sample_duration / 2)) if duration > sample_duration + 2 else 0.0
    )

    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        sample_in = Path(tmp_dir) / "sample_raw.mkv"
        sample_out = Path(tmp_dir) / "sample_hevc.mkv"

        # Step 1 — extract sample (stream copy, instantaneous)
        r1 = _run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(start),
                "-i",
                str(path),
                "-t",
                str(sample_duration),
                "-map",
                "0:v:0",
                "-c",
                "copy",
                str(sample_in),
                "-loglevel",
                "error",
            ]
        )
        if r1.returncode != 0 or not sample_in.exists() or sample_in.stat().st_size == 0:
            return {"error": "sample_extraction_failed"}

        # Step 2 — re-encode sample with VideoToolbox
        r2 = _run_with_progress(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(sample_in),
                "-c:v",
                "hevc_videotoolbox",
                "-q:v",
                str(quality),
                "-tag:v",
                "hvc1",
                "-pix_fmt",
                "p010le",
                "-spatial_aq",
                "1",
                "-allow_sw",
                "0",
                str(sample_out),
                "-loglevel",
                "error",
            ],
            duration=sample_duration,
            callback=callback,
        )
        if r2.returncode != 0 or not sample_out.exists() or sample_out.stat().st_size == 0:
            # Fallback test with libx265 if videotoolbox is unavailable
            r2_fb = _run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(sample_in),
                    "-c:v",
                    "libx265",
                    "-crf",
                    "22",
                    "-preset",
                    "ultrafast",
                    "-pix_fmt",
                    "yuv420p10le",
                    str(sample_out),
                    "-loglevel",
                    "error",
                ]
            )
            if r2_fb.returncode != 0 or not sample_out.exists():
                return {"error": "hevc_encoding_failed"}

        ratio = (
            sample_out.stat().st_size / sample_in.stat().st_size
            if sample_in.stat().st_size
            else 1.0
        )

    estimated_video = video_bytes * ratio
    estimated_total = int(estimated_video + audio_bytes)
    gain_pct = round((1 - estimated_total / original_size) * 100, 1) if original_size else 0.0

    return {
        "original_size": original_size,
        "estimated_size": estimated_total,
        "gain_pct": gain_pct,
        "ratio": round(ratio, 4),
    }
