"""Formatting and string utility helpers for sizes, durations, and terminal labels."""

from __future__ import annotations

import shutil
from typing import Optional


def fmt_bytes(size: float) -> str:
    """Format bytes into human-readable string (KB, MB, GB).

    Args:
        size: Size in bytes.

    Returns:
        Formatted string (e.g. '12.5 MB', '1.45 GB').
    """
    if size < 1_048_576:
        return f"{size / 1024:.1f} KB"
    if size < 1_073_741_824:
        return f"{size / 1_048_576:.1f} MB"
    return f"{size / 1_073_741_824:.2f} GB"


def fmt_duration(seconds: float) -> str:
    """Format duration in seconds into HH:MM:SS or MM:SS.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string (e.g. '1h 24m 30s', '4m 12s' or 'N/A').
    """
    if not seconds or seconds <= 0:
        return "N/A"
    s = int(seconds)
    h, m = divmod(s, 3600)
    m, s = divmod(m, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


def fit_terminal_text(text: str, max_width: int) -> str:
    """Format text to fit within max_width using middle ellipsis if needed.

    Args:
        text: Input string.
        max_width: Maximum allowed width.

    Returns:
        Truncated string with middle ellipsis if longer than max_width.
    """
    if len(text) <= max_width or max_width < 4:
        return text[:max_width]
    part = (max_width - 1) // 2
    rem = max_width - 1 - part
    return f"{text[:part]}…{text[-rem:]}" if rem > 0 else f"{text[: max_width - 1]}…"


def format_file_label(
    name: str,
    extra_width_needed: int = 40,
    term_width: Optional[int] = None,
) -> str:
    """Format file name to dynamically fit terminal width without arbitrary cut-off.

    Args:
        name: File or label name.
        extra_width_needed: Number of characters reserved for progress bars / stats.
        term_width: Optional terminal width override (defaults to shutil.get_terminal_size).

    Returns:
        Formatted and dynamically sized label string.
    """
    if term_width is None:
        term_width = shutil.get_terminal_size((80, 24)).columns
    max_len = max(30, term_width - extra_width_needed)
    return fit_terminal_text(name, max_len)


def send_macos_notification(title: str, message: str) -> None:
    """Send a native macOS desktop notification via AppleScript.

    Args:
        title: Notification title.
        message: Notification message body.
    """
    import subprocess
    import sys

    if sys.platform != "darwin":
        return

    try:
        clean_title = title.replace('"', '\\"')
        clean_msg = message.replace('"', '\\"')
        cmd = [
            "osascript",
            "-e",
            f'display notification "{clean_msg}" with title "{clean_title}" sound name "Glass"',
        ]
        subprocess.run(cmd, capture_output=True, timeout=2.0, check=False)
    except Exception:
        pass
