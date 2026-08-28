"""Unit tests for slim_video.formatting module."""

from __future__ import annotations

from slim_video.formatting import (
    fit_terminal_text,
    fmt_bytes,
    fmt_duration,
    format_file_label,
)


def test_fmt_bytes() -> None:
    assert fmt_bytes(500) == "0.5 KB"
    assert fmt_bytes(1024) == "1.0 KB"
    assert fmt_bytes(1024 * 1024) == "1.0 MB"
    assert fmt_bytes(1024 * 1024 * 1024) == "1.00 GB"
    assert fmt_bytes(2.5 * 1024 * 1024 * 1024) == "2.50 GB"


def test_fmt_duration() -> None:
    assert fmt_duration(0) == "N/A"
    assert fmt_duration(-10) == "N/A"
    assert fmt_duration(45) == "0m 45s"
    assert fmt_duration(125) == "2m 05s"
    assert fmt_duration(3665) == "1h 01m 05s"


def test_fit_terminal_text() -> None:
    short_text = "short.mp4"
    assert fit_terminal_text(short_text, 20) == "short.mp4"

    long_text = "A_Very_Long_Movie_Title_2026_1080p_BluRay.mkv"
    fitted = fit_terminal_text(long_text, 20)
    assert len(fitted) <= 20
    assert "…" in fitted
    assert fitted.startswith("A_Very_Lo")
    assert fitted.endswith("y.mkv")

    # Edge cases
    assert fit_terminal_text("abc", 2) == "ab"


def test_format_file_label() -> None:
    label = format_file_label("Movie (2024).mkv", extra_width_needed=40, term_width=80)
    assert label == "Movie (2024).mkv"

    long_name = "Super_Extremely_Long_Movie_Name_That_Exceeds_Terminal_Width_1080p_x264.mkv"
    truncated_label = format_file_label(long_name, extra_width_needed=40, term_width=70)
    assert len(truncated_label) <= 30
    assert "…" in truncated_label
