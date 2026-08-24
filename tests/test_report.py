"""Unit tests for slim_video.report module."""

from __future__ import annotations

from pathlib import Path

from slim_video.models import BatchSummary, TranscodeRecord
from slim_video.report import format_report, save_report_file


def test_format_report_and_save(tmp_path: Path) -> None:
    summary = BatchSummary(
        directory=tmp_path,
        encoder_name="Apple VideoToolbox (hevc_videotoolbox - 10-bit)",
        start_time="2026-08-24 15:00:00",
        end_time="2026-08-24 15:05:00",
        total_duration_sec=300.0,
        total_files_scanned=2,
        total_files_selected=2,
        total_files_successful=2,
        total_files_failed=0,
        total_original_bytes=4_000_000_000,
        total_final_bytes=1_800_000_000,
        total_saved_bytes=2_200_000_000,
        total_gain_pct=55.0,
        records=[
            TranscodeRecord(
                file_path=str(tmp_path / "movie1.mp4"),
                rel_path="movie1.mp4",
                codec="h264",
                resolution="1920x1080",
                fps=24.0,
                duration=7200.0,
                audio="AAC 2ch",
                original_size=2_000_000_000,
                final_size=900_000_000,
                gain_pct=55.0,
                saved_bytes=1_100_000_000,
                elapsed_seconds=150.0,
                speed="12.5x",
                output_path=str(tmp_path / "movie1.hevc.mkv"),
                quarantine_path=str(tmp_path / "_originals_to_delete" / "movie1.mp4"),
                status="ok",
            ),
            TranscodeRecord(
                file_path=str(tmp_path / "movie2.mkv"),
                rel_path="movie2.mkv",
                codec="h264",
                resolution="1920x1080",
                fps=24.0,
                duration=7200.0,
                audio="AC3 6ch",
                original_size=2_000_000_000,
                final_size=900_000_000,
                gain_pct=55.0,
                saved_bytes=1_100_000_000,
                elapsed_seconds=150.0,
                speed="12.8x",
                output_path=str(tmp_path / "movie2.hevc.mkv"),
                quarantine_path=str(tmp_path / "_originals_to_delete" / "movie2.mkv"),
                status="ok",
            ),
        ],
    )

    report_text = format_report(summary)
    assert "HEVC / x265 TRANSCODING SUMMARY REPORT" in report_text
    assert "55.0%" in report_text
    assert "movie1.mp4" in report_text
    assert "movie2.mkv" in report_text
    assert "_originals_to_delete" in report_text

    main_report = save_report_file(tmp_path, summary)
    assert main_report.exists()
    assert main_report.read_text(encoding="utf-8") == report_text
