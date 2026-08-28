"""Core workflow engine orchestrating scan, sample estimation, interactive selection, and batch execution."""

from __future__ import annotations

import os
import sys
import time
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from slim_video import __version__
from slim_video.constants import DEFAULT_QUALITY, SAMPLE_SECONDS
from slim_video.core import (
    estimate_savings,
    find_h264_candidates,
    get_audio_summary,
    get_duration,
    get_fps,
    get_resolution,
    get_video_codec,
    transcode,
)
from slim_video.formatting import (
    fmt_bytes,
    fmt_duration,
    format_file_label,
    send_macos_notification,
)
from slim_video.history import HistoryManager
from slim_video.models import BatchSummary, FileItem, TranscodeRecord
from slim_video.report import save_report_file
from slim_video.tree_selector import select_files_interactive

console = Console()


def display_estimation_table(
    root: Path,
    items: list[FileItem],
    min_gain: float,
    json_output: bool = False,
) -> None:
    """Print an estimation summary table or JSON for dry-run inspection."""
    total_orig = sum(it.size for it in items)
    total_est = sum(
        (it.estimated_size if it.estimated_size is not None else it.size) for it in items
    )
    saved = max(total_orig - total_est, 0)
    pct = round((saved / total_orig) * 100, 1) if total_orig else 0.0

    if json_output:
        import json

        data = {
            "directory": str(root),
            "total_files": len(items),
            "total_original_bytes": total_orig,
            "total_estimated_bytes": total_est,
            "total_saved_bytes": saved,
            "total_gain_pct": pct,
            "min_gain_threshold": min_gain,
            "files": [
                {
                    "path": str(it.path),
                    "rel_path": str(it.rel_path),
                    "codec": it.codec,
                    "resolution": it.resolution,
                    "fps": it.fps,
                    "original_size": it.size,
                    "estimated_size": it.estimated_size,
                    "estimated_gain_pct": it.estimated_gain_pct,
                    "recommended": (
                        it.estimated_gain_pct is not None and it.estimated_gain_pct >= min_gain
                    ),
                }
                for it in items
            ],
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(
        title=f"📊 Potential Space Savings Estimation ({root.name})",
        expand=True,
        border_style="cyan",
    )
    table.add_column("Video File", style="cyan", no_wrap=False, overflow="fold")
    table.add_column("Format", style="dim", justify="center")
    table.add_column("Original", justify="right")
    table.add_column("Est. HEVC", justify="right")
    table.add_column("Est. Gain", justify="right", style="bold")
    table.add_column("Recommendation", justify="center")

    eligible_count = 0

    for it in items:
        est = it.estimated_size if it.estimated_size is not None else it.size
        gain_str = f"-{it.estimated_gain_pct:.1f}%" if it.estimated_gain_pct is not None else "N/A"
        if it.estimated_gain_pct is not None and it.estimated_gain_pct >= min_gain:
            rec = "[bold green]✅ Transcode[/bold green]"
            gain_styled = f"[green]{gain_str}[/green]"
            eligible_count += 1
        elif it.estimated_gain_pct is not None:
            rec = f"[yellow]⏭ Skip (< {min_gain}%)[/yellow]"
            gain_styled = f"[yellow]{gain_str}[/yellow]"
        else:
            rec = "[dim]Unknown[/dim]"
            gain_styled = f"[dim]{gain_str}[/dim]"

        table.add_row(
            str(it.rel_path),
            f"{it.codec} ({it.resolution})",
            fmt_bytes(it.size),
            fmt_bytes(est),
            gain_styled,
            rec,
        )

    console.print(table)

    console.print(
        Panel(
            f"Candidate Files Scanned : [bold]{len(items)} file(s)[/bold] ({fmt_bytes(total_orig)})\n"
            f"Recommended to Transcode: [bold green]{eligible_count} file(s)[/bold green]\n"
            f"Estimated Projected Size: [bold]{fmt_bytes(total_est)}[/bold]\n"
            f"Total Projected Savings : [bold green]{fmt_bytes(saved)}[/bold green] ([bold green]-{pct}%[/bold green])\n\n"
            f"[dim]To perform the actual transcoding, run: [bold cyan]slim-video '{root}'[/bold cyan][/dim]",
            title="✨ Dry-Run Estimation Results",
            border_style="green",
        )
    )


def execute_batch(
    root: Path,
    items: list[FileItem],
    total_scanned: int,
    quality: int,
    history_manager: Optional[HistoryManager] = None,
    delete_original: bool = False,
    staging_dir: Optional[Path] = None,
) -> BatchSummary:
    """Execute batch transcoding, display progress, and write text report."""
    if history_manager is None:
        history_manager = HistoryManager()

    staging_msg = f" [dim](SSD staging: {staging_dir})[/dim]" if staging_dir else ""
    console.print(
        f"\n[bold green]🚀  Starting batch transcoding for {len(items)} file(s)…[/bold green]{staging_msg}\n"
    )

    start_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    start_perf = time.perf_counter()

    summary = BatchSummary(
        directory=root,
        encoder_name="Apple VideoToolbox (hevc_videotoolbox - 10-bit)",
        start_time=start_timestamp,
        total_files_scanned=total_scanned,
        total_files_selected=len(items),
        delete_original=delete_original,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        batch_task = progress.add_task("Batch Progress", total=len(items))
        file_task = progress.add_task("Current File", total=100)

        for item in items:
            f = item.path
            orig_size = item.size
            duration = item.duration

            last_speed = ["1.0x"]
            file_start = time.perf_counter()

            def _progress_cb(
                pct: float,
                elapsed: float,
                speed: str,
                _f: Path = f,
                _dur: float = duration,
                _ls: list[str] = last_speed,
            ) -> None:
                _ls[0] = speed
                disp_curr = format_file_label(_f.name, extra_width_needed=45)
                progress.update(
                    file_task,
                    completed=pct,
                    description=(
                        f"[bold cyan]{disp_curr}[/bold cyan] "
                        f"[green]{pct:.1f}%[/green] "
                        f"{fmt_duration(elapsed)}/{fmt_duration(_dur)} "
                        f"@ [yellow]{speed}[/yellow]"
                    ),
                )

            def _status_cb(msg: str, _f: Path = f) -> None:
                disp_curr = format_file_label(_f.name, extra_width_needed=40)
                progress.update(
                    file_task,
                    description=f"[bold cyan]{disp_curr}[/bold cyan] — {msg}",
                )

            disp_start = format_file_label(f.name, extra_width_needed=40)
            progress.update(
                file_task,
                completed=0,
                description=f"[bold cyan]{disp_start}[/bold cyan] — starting…",
            )

            result = transcode(
                src=f,
                library_root=root,
                quality=quality,
                progress_callback=_progress_cb,
                status_callback=_status_cb,
                delete_original=delete_original,
                staging_dir=staging_dir,
            )

            file_elapsed = max(time.perf_counter() - file_start, 0.1)
            progress.update(file_task, completed=100)

            if result["status"] == "ok":
                final_size = result["output_size"]
                saved = max(orig_size - final_size, 0)
                gain = round((saved / orig_size) * 100, 1) if orig_size else 0.0

                record = TranscodeRecord(
                    file_path=str(f),
                    rel_path=str(item.rel_path),
                    codec=item.codec,
                    resolution=item.resolution,
                    fps=item.fps,
                    duration=duration,
                    audio=item.audio,
                    original_size=orig_size,
                    final_size=final_size,
                    gain_pct=gain,
                    saved_bytes=saved,
                    elapsed_seconds=file_elapsed,
                    speed=last_speed[0],
                    output_path=result.get("output_path"),
                    quarantine_path=result.get("quarantine_path"),
                    deleted_original=result.get("deleted_original", False),
                    status="ok",
                )
                summary.total_files_successful += 1
                summary.total_original_bytes += orig_size
                summary.total_final_bytes += final_size
                summary.total_saved_bytes += saved
                summary.records.append(record)

                history_manager.record_transcode(
                    file_path=str(item.path),
                    codec=item.codec,
                    original_size=orig_size,
                    final_size=final_size,
                    gain_pct=gain,
                    status="ok",
                    quality=quality,
                )
            else:
                record = TranscodeRecord(
                    file_path=str(f),
                    rel_path=str(item.rel_path),
                    codec=item.codec,
                    resolution=item.resolution,
                    fps=item.fps,
                    duration=duration,
                    audio=item.audio,
                    original_size=orig_size,
                    final_size=0,
                    gain_pct=0.0,
                    saved_bytes=0,
                    elapsed_seconds=file_elapsed,
                    speed="N/A",
                    output_path=None,
                    quarantine_path=None,
                    status="error",
                    error_message=result.get("error_message") or result.get("error"),
                )
                summary.total_files_failed += 1
                summary.records.append(record)

                history_manager.record_transcode(
                    file_path=str(item.path),
                    codec=item.codec,
                    original_size=orig_size,
                    final_size=0,
                    gain_pct=0.0,
                    status="error",
                    quality=quality,
                )

            progress.advance(batch_task)

    summary.total_duration_sec = time.perf_counter() - start_perf
    if summary.total_original_bytes > 0:
        summary.total_gain_pct = round(
            (summary.total_saved_bytes / summary.total_original_bytes) * 100, 1
        )

    # Save detailed text report
    report_file = save_report_file(root, summary)

    # Display final summary table & panel
    _display_batch_summary_panel(root, summary, report_file)

    # Native macOS desktop notification
    if summary.total_files_successful > 0:
        notif_msg = (
            f"{summary.total_files_successful} video(s) converted "
            f"({fmt_bytes(summary.total_saved_bytes)} freed, -{summary.total_gain_pct}%)"
        )
        send_macos_notification(title="slim-video complete 🎉", message=notif_msg)

    return summary


def _display_batch_summary_panel(root: Path, summary: BatchSummary, report_file: Path) -> None:
    """Print the final completion panel and table after batch transcode."""
    console.print(
        Panel(
            f"[bold green]Batch Transcoding Complete in {fmt_duration(summary.total_duration_sec)}![/bold green]\n\n"
            f"  • Successful           : [bold green]{summary.total_files_successful}/{summary.total_files_selected} file(s)[/bold green]\n"
            + (
                f"  • Failed / Errors      : [bold red]{summary.total_files_failed} file(s)[/bold red]\n"
                if summary.total_files_failed > 0
                else ""
            )
            + f"  • Original Size        : [bold]{fmt_bytes(summary.total_original_bytes)}[/bold]\n"
            f"  • New HEVC Size        : [bold]{fmt_bytes(summary.total_final_bytes)}[/bold]\n"
            f"  • Disk Space Freed     : [bold green]{fmt_bytes(summary.total_saved_bytes)}[/bold green] "
            f"([bold green]-{summary.total_gain_pct:.1f}%[/bold green])\n"
            + (
                "  • Original Files       : [bold red]Permanently Deleted after encoding[/bold red]\n"
                if summary.delete_original
                else f"  • Quarantine Folder    : [cyan]{root / '_originals_to_delete'}[/cyan]\n"
            )
            + f"  • Full Report File     : [cyan]{report_file}[/cyan]",
            title="✨ Batch Complete",
            border_style="green",
        )
    )

    table = Table(
        title="📋 Detailed Transcode Summary",
        expand=True,
        border_style="green",
    )
    table.add_column("File", style="cyan", no_wrap=False, overflow="fold")
    table.add_column("Original", justify="right")
    table.add_column("New HEVC", justify="right")
    table.add_column("Space Saved", justify="right", style="bold green")
    table.add_column("Time", justify="right")
    table.add_column("Speed", justify="center")
    table.add_column("Status", justify="center")

    for r in summary.records:
        status_styled = (
            "[bold green]OK[/bold green]"
            if r.status == "ok"
            else f"[bold red]ERR ({r.error_message})[/bold red]"
        )
        table.add_row(
            r.rel_path,
            fmt_bytes(r.original_size),
            fmt_bytes(r.final_size) if r.status == "ok" else "—",
            fmt_bytes(r.saved_bytes) if r.status == "ok" else "—",
            fmt_duration(r.elapsed_seconds),
            r.speed,
            status_styled,
        )

    console.print(table)
    console.print()


def run_main_workflow(
    path_arg: Optional[str] = None,
    min_gain: float = 10.0,
    quality: int = DEFAULT_QUALITY,
    sample_seconds: int = SAMPLE_SECONDS,
    run_samples: bool = True,
    yes: bool = False,
    dry_run: bool = False,
    all_codecs: bool = False,
    delete_original: bool = False,
    staging_dir: Optional[Path] = None,
    history_manager: Optional[HistoryManager] = None,
    interactive_folder_prompt: Optional[Callable[[], str]] = None,
    find_candidates_fn: Optional[Callable[..., tuple[list[Path], list[Path]]]] = None,
    json_output: bool = False,
) -> None:
    """Execute the core workflow: scan -> sample evaluation -> interactive tree -> transcode -> report."""
    if history_manager is None:
        history_manager = HistoryManager()

    is_interactive = sys.stdin.isatty() and sys.stdout.isatty()
    if not is_interactive and not yes and not dry_run:
        console.print("[dim]Non-interactive environment detected: running in automated mode.[/dim]")
        yes = True

    if not path_arg:
        if is_interactive and not yes and interactive_folder_prompt:
            path_arg = interactive_folder_prompt()
        else:
            path_arg = os.getcwd()

    root = Path(path_arg).resolve()
    if not root.exists() or not root.is_dir():
        if json_output:
            import json

            print(json.dumps({"error": f"Directory not found: {root}"}))
            return
        console.print(
            Panel(
                f"[bold red]❌ Directory not found:[/bold red] [yellow]{root}[/yellow]\n\n"
                "Please verify the path and ensure the folder exists.",
                title="⚠️ Invalid Folder",
                border_style="red",
            )
        )
        return

    if not json_output:
        mode_tag = "[bold yellow][DRY-RUN / ESTIMATION ONLY][/bold yellow] " if dry_run else ""
        staging_tag = f" · SSD Staging: {staging_dir}" if staging_dir else ""
        console.print(
            Panel.fit(
                f"{mode_tag}[bold cyan]slim-video[/bold cyan] [dim]v{__version__}[/dim] ── "
                "[bold white]H.264 → x265 (HEVC) Auto Transcoder[/bold white]\n"
                f"[dim]Sample Test: {sample_seconds}s (mid-point) · Min Gain Threshold: {min_gain}%{staging_tag} · Apple Silicon VideoToolbox[/dim]",
                border_style="yellow" if dry_run else "cyan",
            )
        )

    # 1. Scan files with animated spinner & real-time file discovery
    scan_status_ctx = (
        console.status(
            f"[bold cyan]🔍 Scanning files in[/bold cyan] [yellow]{root.name}/[/yellow]…",
            spinner="dots",
        )
        if not json_output
        else nullcontext()
    )

    with scan_status_ctx:

        def _scan_progress(cur_file: Path, cand_count: int, hevc_count: int) -> None:
            if not json_output and hasattr(scan_status_ctx, "update"):
                disp_name = format_file_label(cur_file.name, extra_width_needed=45)
                scan_status_ctx.update(
                    f"[bold cyan]🔍 Scanning directory…[/bold cyan] [yellow]{disp_name}[/yellow] "
                    f"[dim]({cand_count} candidates, {hevc_count} HEVC found)[/dim]"
                )

        scan_fn = find_candidates_fn if find_candidates_fn is not None else find_h264_candidates
        candidates, already_hevc = scan_fn(
            root, all_codecs=all_codecs, progress_callback=_scan_progress
        )

    if already_hevc and not json_output:
        console.print(
            f"[green]✓  {len(already_hevc)} video file(s) already encoded in HEVC/x265 (skipped).[/green]"
        )

    if not candidates:
        if json_output:
            import json

            print(
                json.dumps(
                    {
                        "directory": str(root),
                        "total_files": 0,
                        "already_hevc": [str(p) for p in already_hevc],
                        "files": [],
                    }
                )
            )
            return

        if already_hevc:
            console.print(
                Panel(
                    "[bold green]🎉 All video files in this folder are already optimized in HEVC![/bold green]\n"
                    "No further transcoding is needed.",
                    title="✨ Perfectly Optimized",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[yellow]No H.264 video files found in:[/yellow] [cyan]{root}[/cyan]\n\n"
                    "[dim]Tip: If your videos use other formats (e.g. MPEG-4, VC-1), use the [bold]--all-codecs[/bold] flag.[/dim]",
                    title="ℹ️ No Files Found",
                    border_style="yellow",
                )
            )
        return

    # 2. Probe metadata & run 20s middle sample evaluation with live animation
    if not json_output:
        console.print(
            f"[bold blue]🧪  Evaluating {len(candidates)} candidate file(s) "
            f"({sample_seconds}s sample test at mid-point)…[/bold blue]"
        )

    file_items: list[FileItem] = []
    below_thresh_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        disable=json_output,
    ) as progress:
        task = progress.add_task("Evaluating videos…", total=len(candidates))

        for f in candidates:
            try:
                rel = f.relative_to(root)
            except ValueError:
                rel = Path(f.name)

            codec = get_video_codec(f) or "h264"
            res = get_resolution(f)
            fps = get_fps(f)
            dur = get_duration(f)
            audio = get_audio_summary(f)
            size = f.stat().st_size if f.exists() else 0

            disp_f = format_file_label(f.name, extra_width_needed=35)
            progress.update(
                task,
                description=(
                    f"Analyzing [bold cyan]{disp_f}[/bold cyan] [dim]({codec} · {res})[/dim]…"
                ),
            )

            est_size: Optional[int] = None
            est_gain: Optional[float] = None
            below_thresh = False
            selected = True

            if run_samples and size > 0:

                def _sample_cb(pct: float, _elapsed: float, speed: str, _f: Path = f) -> None:
                    disp_sub = format_file_label(_f.name, extra_width_needed=35)
                    progress.update(
                        task,
                        description=(
                            f"Sample [bold cyan]{disp_sub}[/bold cyan] "
                            f"[green]{pct:3.0f}%[/green] @ [yellow]{speed}[/yellow]"
                        ),
                    )

                est_res = estimate_savings(
                    path=f,
                    quality=quality,
                    sample_seconds=sample_seconds,
                    callback=_sample_cb,
                )

                if "error" not in est_res:
                    est_size = est_res["estimated_size"]
                    est_gain = est_res["gain_pct"]
                    if est_gain < min_gain:
                        below_thresh = True
                        selected = False  # Auto-uncheck: gain < threshold
                        below_thresh_count += 1
                    else:
                        selected = True

                    history_manager.record_test(
                        file_path=str(f),
                        codec=codec,
                        original_size=est_res["original_size"],
                        estimated_size=est_size,
                        gain_pct=est_gain,
                        ratio=est_res["ratio"],
                        quality=quality,
                    )

            file_items.append(
                FileItem(
                    path=f,
                    rel_path=rel,
                    size=size,
                    codec=codec,
                    resolution=res,
                    fps=fps,
                    duration=dur,
                    audio=audio,
                    selected=selected,
                    estimated_size=est_size,
                    estimated_gain_pct=est_gain,
                    below_threshold=below_thresh,
                )
            )
            progress.advance(task)

    if below_thresh_count > 0 and not json_output:
        console.print(
            f"[dim]ℹ️  {below_thresh_count} file(s) had an estimated gain < {min_gain}% and were automatically unchecked.[/dim]"
        )

    # 3. Dry-Run Table display if estimate-only requested
    if dry_run:
        display_estimation_table(
            root=root,
            items=file_items,
            min_gain=min_gain,
            json_output=json_output,
        )
        return

    # 4. Interactive Collapsible Tree Selector
    console.print(
        f"\n[bold green]Found {len(file_items)} candidate file(s). Opening interactive tree selection…[/bold green]"
    )

    selected_items = select_files_interactive(
        root=root,
        file_items=file_items,
        non_interactive=yes,
    )

    if not selected_items:
        console.print("[yellow]No files selected. Transcoding aborted.[/yellow]\n")
        return

    # 5. Pre-transcode summary
    total_selected_size = sum(item.size for item in selected_items)
    total_selected_est = sum(
        (item.estimated_size if item.estimated_size is not None else item.size)
        for item in selected_items
    )
    est_saving = max(total_selected_size - total_selected_est, 0)
    est_pct = round((est_saving / total_selected_size) * 100, 1) if total_selected_size else 0.0

    action_item = (
        "  • Original Files Action : [bold red]Permanently Deleted after encode (Direct Deletion Mode)[/bold red]\n"
        if delete_original
        else f"  • Quarantine Folder     : [cyan]{root / '_originals_to_delete'}[/cyan]\n"
    )

    staging_item = (
        f"  • SSD Staging Directory : [cyan]{staging_dir}[/cyan]\n" if staging_dir else ""
    )
    console.print(
        Panel(
            f"[bold green]Ready to transcode {len(selected_items)} file(s) to x265 (HEVC)[/bold green]\n\n"
            f"  • Source Total Size     : [bold]{fmt_bytes(total_selected_size)}[/bold]\n"
            f"  • Projected HEVC Size   : [bold]{fmt_bytes(total_selected_est)}[/bold] "
            f"([bold green]Est. Saved: {fmt_bytes(est_saving)} / -{est_pct}%[/bold green])\n"
            f"  • Video Encoder         : VideoToolbox 10-bit HEVC (Quality: {quality})\n"
            f"  • Audio / Subtitles     : Stream Copied (100% Lossless)\n"
            f"{staging_item}"
            f"{action_item}"
            f"  • Summary Report        : Will be saved to [cyan]{root / 'transcode_report.txt'}[/cyan]",
            title="📋  Transcode Summary",
            border_style="yellow" if delete_original else "green",
        )
    )

    if not yes:
        prompt_msg = (
            f"[bold red]⚠️  Delete originals & transcode[/bold red] {len(selected_items)} file(s)?"
            if delete_original
            else f"Start hardware transcoding {len(selected_items)} file(s)?"
        )
        confirmed = inquirer.confirm(
            message=prompt_msg,
            default=True,
        ).execute()
        if not confirmed:
            console.print("[yellow]Aborted by user.[/yellow]\n")
            return

    # 6. Run Transcoding Batch
    execute_batch(
        root=root,
        items=selected_items,
        total_scanned=len(file_items),
        quality=quality,
        history_manager=history_manager,
        delete_original=delete_original,
        staging_dir=staging_dir,
    )
