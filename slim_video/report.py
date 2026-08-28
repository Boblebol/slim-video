"""Detailed text report generator for HEVC batch transcoding sessions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from slim_video.formatting import fmt_bytes, fmt_duration
from slim_video.models import BatchSummary


def format_report(summary: BatchSummary) -> str:
    """Generate a clean, readable text report from a BatchSummary."""
    lines: list[str] = []
    bar = "=" * 80
    subbar = "-" * 80

    lines.append(bar)
    lines.append("                  HEVC / x265 TRANSCODING SUMMARY REPORT")
    lines.append(bar)
    lines.append(f"Date & Time:        {summary.start_time}")
    lines.append(f"Target Directory:   {summary.directory}")
    lines.append(f"Video Encoder:      {summary.encoder_name}")
    lines.append(f"Total Batch Time:   {fmt_duration(summary.total_duration_sec)}")
    lines.append("")

    lines.append(bar)
    lines.append("                              GLOBAL STORAGE GAIN")
    lines.append(bar)
    lines.append(
        f"Files Selected:     {summary.total_files_selected} / {summary.total_files_scanned} candidate(s)"
    )
    lines.append(f"Transcoded OK:      {summary.total_files_successful} file(s)")
    if summary.total_files_failed > 0:
        lines.append(f"Errors / Failed:    {summary.total_files_failed} file(s)")
    lines.append("")
    lines.append(
        f"Original Total Size:  {fmt_bytes(summary.total_original_bytes)} ({summary.total_original_bytes:,} bytes)"
    )
    lines.append(
        f"New HEVC Total Size:  {fmt_bytes(summary.total_final_bytes)} ({summary.total_final_bytes:,} bytes)"
    )
    lines.append(
        f"Storage Freed:        {fmt_bytes(summary.total_saved_bytes)} ({summary.total_saved_bytes:,} bytes)"
    )
    lines.append(f"Overall Reduction:    -{summary.total_gain_pct:.1f}%")
    lines.append("")

    lines.append(bar)
    lines.append("                             DETAILED FILE BREAKDOWN")
    lines.append(bar)

    if not summary.records:
        lines.append("No files were transcoded.")
    else:
        for idx, rec in enumerate(summary.records, 1):
            status_tag = (
                "SUCCESS" if rec.status == "ok" else "ERROR" if rec.status == "error" else "SKIPPED"
            )
            lines.append(f"[{idx}/{len(summary.records)}] {rec.rel_path}")
            lines.append(f"  • Status         : {status_tag}")
            lines.append(
                f"  • Video Spec     : {rec.codec.upper()} -> HEVC 10-bit ({rec.resolution} @ {rec.fps:.2f} fps)"
            )
            lines.append(f"  • Audio / Subs   : {rec.audio} (Stream Copied - Lossless)")
            lines.append(
                f"  • Original Size  : {fmt_bytes(rec.original_size)} ({rec.original_size:,} bytes)"
            )
            if rec.status == "ok":
                lines.append(
                    f"  • New HEVC Size  : {fmt_bytes(rec.final_size)} ({rec.final_size:,} bytes)"
                )
                lines.append(
                    f"  • Space Saved    : {fmt_bytes(rec.saved_bytes)} (-{rec.gain_pct:.1f}%)"
                )
                lines.append(
                    f"  • Encode Time    : {fmt_duration(rec.elapsed_seconds)} (Speed: {rec.speed})"
                )
                if rec.output_path:
                    lines.append(f"  • Output Video   : {rec.output_path}")
                if rec.deleted_original:
                    lines.append("  • Original Action: DELETED directly after encode")
                elif rec.quarantine_path:
                    lines.append(f"  • Original Moved : {rec.quarantine_path}")
            elif rec.error_message:
                lines.append(f"  • Error Reason   : {rec.error_message}")
            lines.append(subbar)

    lines.append("")
    lines.append(bar)
    lines.append("                              STORAGE & SAFETY NOTICE")
    lines.append(bar)
    if summary.delete_original:
        lines.append("Original files WERE permanently deleted after successful encoding.")
        lines.append(
            f"A total of {fmt_bytes(summary.total_saved_bytes)} of physical storage was immediately freed."
        )
    else:
        quarantine_dir = summary.directory / "_originals_to_delete"
        lines.append("Original files were NOT permanently deleted.")
        lines.append("They were safely moved to the quarantine folder:")
        lines.append(f"  {quarantine_dir}")
        lines.append("")
        lines.append("Instructions:")
        lines.append("1. Verify the playback and audio quality of your new .hevc.mkv videos.")
        lines.append(
            "2. Once satisfied, you can safely delete the '_originals_to_delete' directory"
        )
        lines.append(f"   to reclaim {fmt_bytes(summary.total_saved_bytes)} of physical storage.")
    lines.append(bar)
    lines.append("")

    return "\n".join(lines)


def save_report_file(directory: Path, summary: BatchSummary) -> Path:
    """Save the transcode report to the directory and return the file path."""
    directory.mkdir(parents=True, exist_ok=True)
    report_text = format_report(summary)

    # Main report file
    main_report_path = directory / "transcode_report.txt"
    try:
        main_report_path.write_text(report_text, encoding="utf-8")
    except Exception as exc:
        print(f"[report] Warning: could not write main report: {exc}")

    # Timestamped archive report
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archive_report_path = directory / f"transcode_report_{timestamp_str}.txt"
    try:
        archive_report_path.write_text(report_text, encoding="utf-8")
    except Exception:
        pass

    return main_report_path
