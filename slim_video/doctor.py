"""System diagnostics and hardware validation module for slim-video.

Verifies that the system environment, binaries (ffmpeg, ffprobe), Apple Silicon
hardware acceleration (VideoToolbox), and fast temp storage are correctly configured
and runnable.
"""

from __future__ import annotations

import locale
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from slim_video.models import DoctorCheckResult


def check_python_version() -> DoctorCheckResult:
    """Check that Python version is 3.9 or newer."""
    v = sys.version_info
    passed = (v.major, v.minor) >= (3, 9)
    return DoctorCheckResult(
        name="Python Version",
        passed=passed,
        details=f"Python {v.major}.{v.minor}.{v.micro} ({platform.python_implementation()})",
        critical=True,
    )


def check_platform() -> DoctorCheckResult:
    """Check operating system and CPU architecture."""
    system = platform.system()
    machine = platform.machine()
    is_mac = system == "Darwin"
    details = f"{system} {platform.release()} ({machine})"
    if is_mac and machine == "arm64":
        details += " [Apple Silicon M-Series]"

    return DoctorCheckResult(
        name="Operating System & Architecture",
        passed=True,
        details=details,
        critical=False,
    )


def check_ffmpeg_binary() -> DoctorCheckResult:
    """Check that ffmpeg is installed and executable."""
    path = shutil.which("ffmpeg")
    if not path:
        return DoctorCheckResult(
            name="FFmpeg Binary",
            passed=False,
            details="Not found in PATH. Install with: brew install ffmpeg",
            critical=True,
        )

    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=False)
        first_line = res.stdout.splitlines()[0] if res.stdout else "Version unknown"
        return DoctorCheckResult(
            name="FFmpeg Binary",
            passed=True,
            details=f"Found at {path} ({first_line})",
            critical=True,
        )
    except Exception as exc:
        return DoctorCheckResult(
            name="FFmpeg Binary",
            passed=False,
            details=f"Error executing ffmpeg: {exc}",
            critical=True,
        )


def check_ffprobe_binary() -> DoctorCheckResult:
    """Check that ffprobe is installed and executable."""
    path = shutil.which("ffprobe")
    if not path:
        return DoctorCheckResult(
            name="FFprobe Binary",
            passed=False,
            details="Not found in PATH. Install with: brew install ffmpeg",
            critical=True,
        )

    try:
        res = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, check=False)
        first_line = res.stdout.splitlines()[0] if res.stdout else "Version unknown"
        return DoctorCheckResult(
            name="FFprobe Binary",
            passed=True,
            details=f"Found at {path} ({first_line})",
            critical=True,
        )
    except Exception as exc:
        return DoctorCheckResult(
            name="FFprobe Binary",
            passed=False,
            details=f"Error executing ffprobe: {exc}",
            critical=True,
        )


def check_videotoolbox_support() -> DoctorCheckResult:
    """Check that ffmpeg supports hevc_videotoolbox hardware encoder."""
    if not shutil.which("ffmpeg"):
        return DoctorCheckResult(
            name="VideoToolbox Hardware Encoder",
            passed=False,
            details="Skipped (ffmpeg missing)",
            critical=True,
        )

    try:
        res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, check=False)
        has_vt = "hevc_videotoolbox" in res.stdout
        has_x265 = "libx265" in res.stdout

        if has_vt:
            return DoctorCheckResult(
                name="VideoToolbox Hardware Encoder",
                passed=True,
                details="hevc_videotoolbox available (Hardware-accelerated)",
                critical=True,
            )
        elif has_x265:
            return DoctorCheckResult(
                name="VideoToolbox Hardware Encoder",
                passed=True,
                details="hevc_videotoolbox missing, but libx265 is available as fallback",
                critical=False,
            )
        else:
            return DoctorCheckResult(
                name="VideoToolbox Hardware Encoder",
                passed=False,
                details="No HEVC encoder found (neither hevc_videotoolbox nor libx265)",
                critical=True,
            )
    except Exception as exc:
        return DoctorCheckResult(
            name="VideoToolbox Hardware Encoder",
            passed=False,
            details=f"Error checking encoders: {exc}",
            critical=True,
        )


def check_temp_storage() -> DoctorCheckResult:
    """Check that /tmp is writable for fast sample encoding."""
    try:
        with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
            test_file = Path(tmp_dir) / "test.tmp"
            test_file.write_text("ok", encoding="utf-8")
            passed = test_file.exists() and test_file.read_text(encoding="utf-8") == "ok"
            return DoctorCheckResult(
                name="Temporary SSD Storage (/tmp)",
                passed=passed,
                details=f"Write & read access OK ({tmp_dir})",
                critical=True,
            )
    except Exception as exc:
        return DoctorCheckResult(
            name="Temporary SSD Storage (/tmp)",
            passed=False,
            details=f"Cannot write to /tmp: {exc}",
            critical=True,
        )


def check_curses_terminal() -> DoctorCheckResult:
    """Check that curses library and terminal locale are properly initialized."""
    try:
        loc = locale.setlocale(locale.LC_ALL, "")
        import curses  # noqa: F401

        return DoctorCheckResult(
            name="Terminal & Curses Support",
            passed=True,
            details=f"Curses loaded successfully with locale {loc}",
            critical=False,
        )
    except Exception as exc:
        return DoctorCheckResult(
            name="Terminal & Curses Support",
            passed=False,
            details=f"Curses initialization warning: {exc}",
            critical=False,
        )


def run_hardware_transcode_benchmark() -> DoctorCheckResult:
    """Execute a real 1-second synthetic hardware transcode test to verify execution."""
    if not shutil.which("ffmpeg"):
        return DoctorCheckResult(
            name="Live Hardware Transcode Benchmark",
            passed=False,
            details="Skipped (ffmpeg missing)",
            critical=True,
        )

    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_dir:
        input_mp4 = Path(tmp_dir) / "bench_h264.mp4"
        output_mkv = Path(tmp_dir) / "bench_hevc.mkv"

        try:
            # 1. Generate 1s synthetic H.264 video
            r1 = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc=duration=1:size=640x360:rate=30",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    str(input_mp4),
                    "-loglevel",
                    "error",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if r1.returncode != 0 or not input_mp4.exists():
                return DoctorCheckResult(
                    name="Live Hardware Transcode Benchmark",
                    passed=False,
                    details=f"Failed to generate synthetic test video: {r1.stderr}",
                    critical=True,
                )

            # 2. Transcode with VideoToolbox
            t0 = time.perf_counter()
            r2 = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(input_mp4),
                    "-c:v",
                    "hevc_videotoolbox",
                    "-q:v",
                    "50",
                    "-tag:v",
                    "hvc1",
                    "-pix_fmt",
                    "p010le",
                    "-spatial_aq",
                    "1",
                    str(output_mkv),
                    "-loglevel",
                    "error",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            elapsed = time.perf_counter() - t0

            if r2.returncode != 0 or not output_mkv.exists() or output_mkv.stat().st_size == 0:
                # Fallback test with libx265
                r2_fb = subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(input_mp4),
                        "-c:v",
                        "libx265",
                        "-crf",
                        "22",
                        "-preset",
                        "ultrafast",
                        str(output_mkv),
                        "-loglevel",
                        "error",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if r2_fb.returncode == 0 and output_mkv.exists():
                    return DoctorCheckResult(
                        name="Live Hardware Transcode Benchmark",
                        passed=True,
                        details=f"Software transcode (libx265) completed in {elapsed:.2f}s",
                        critical=False,
                    )
                return DoctorCheckResult(
                    name="Live Hardware Transcode Benchmark",
                    passed=False,
                    details=f"Transcode execution failed: {r2.stderr}",
                    critical=True,
                )

            fps_approx = 30 / elapsed if elapsed > 0 else 0
            return DoctorCheckResult(
                name="Live Hardware Transcode Benchmark",
                passed=True,
                details=f"VideoToolbox test passed! (1s encoded in {elapsed * 1000:.1f}ms ≈ {fps_approx:.0f} fps)",
                critical=True,
            )

        except Exception as exc:
            return DoctorCheckResult(
                name="Live Hardware Transcode Benchmark",
                passed=False,
                details=f"Benchmark error: {exc}",
                critical=True,
            )


def run_all_doctor_checks(include_benchmark: bool = True) -> list[DoctorCheckResult]:
    """Run all diagnostic checks and return results list."""
    checks = [
        check_python_version(),
        check_platform(),
        check_ffmpeg_binary(),
        check_ffprobe_binary(),
        check_videotoolbox_support(),
        check_temp_storage(),
        check_curses_terminal(),
    ]
    if include_benchmark:
        checks.append(run_hardware_transcode_benchmark())
    return checks
