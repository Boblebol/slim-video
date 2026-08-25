"""slim-video — Smart, hardware-accelerated H.264 to HEVC batch transcoder for Apple Silicon.

Features:
- Scans directories recursively for H.264/AVC videos
- Evaluates candidate files with a real 20-second sample encode in the middle
- Automatically flags and deselects files with < 10% extrapolated gain ("ça ne vaut pas le coup")
- Interactive collapsible Tree View with checkboxes to fold/unfold & select files
- Automatic hardware-accelerated x265 compression preserving source quality
- Lossless copy of all audio tracks and subtitles
- Detailed summary text report of disk space gained
- Persistent and explicit configuration file manageable via `slim-video config`
- Built-in environment & hardware diagnostics via `slim-video doctor`
- Safe quarantine of original files (never permanently deletes without user consent)
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
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
)
from rich.table import Table

from slim_video import __author__, __github__, __url__, __version__
from slim_video.config import config_manager
from slim_video.core import (
    DEFAULT_QUALITY,
    SAMPLE_SECONDS,
    check_dependencies,
    estimate_savings,
    find_h264_candidates,
    get_audio_summary,
    get_duration,
    get_fps,
    get_resolution,
    get_video_codec,
    transcode,
)
from slim_video.doctor import check_videotoolbox_support, run_all_doctor_checks
from slim_video.history import HistoryManager
from slim_video.models import BatchSummary, FileItem, TranscodeRecord
from slim_video.report import save_report_file
from slim_video.tree_selector import (
    fit_terminal_text,
    fmt_bytes,
    fmt_duration,
    select_files_interactive,
)

# ---------------------------------------------------------------------------
# App Bootstrap & Styling
# ---------------------------------------------------------------------------

console = Console()


def format_file_label(name: str, extra_width_needed: int = 40) -> str:
    """Format file name to dynamically fit terminal width without arbitrary cut-off."""
    term_width = console.width if console.width else 80
    max_len = max(30, term_width - extra_width_needed)
    return fit_terminal_text(name, max_len)


CLI_HELP_EPILOG = """
[bold yellow]💡 Examples & Quick Commands:[/bold yellow]
  [cyan]slim-video[/cyan]                          # Open interactive directory picker & menu
  [cyan]slim-video /Volumes/Films[/cyan]           # Scan, sample-test, and transcode a specific folder
  [cyan]slim-video estimate /Volumes/Films[/cyan]  # Quick estimation only without touching original files
  [cyan]slim-video doctor[/cyan]                   # Verify Apple Silicon VideoToolbox acceleration
  [cyan]slim-video config wizard[/cyan]            # Step-by-step interactive configuration wizard
  [cyan]slim-video history[/cyan]                  # View cumulative space saved across all sessions
"""

app = typer.Typer(
    name="slim-video",
    help="🎬 [bold cyan]slim-video[/bold cyan] — Smart H.264 to HEVC/x265 Batch Transcoder for Apple Silicon.",
    epilog=CLI_HELP_EPILOG,
    rich_markup_mode="rich",
    add_completion=False,
    no_args_is_help=False,
)
history = HistoryManager()


def _version_callback(value: bool) -> None:
    """Print formatted version banner and exit."""
    if value:
        vtb_check = check_videotoolbox_support()
        vtb_status = (
            "[bold green]✅ Available (hevc_videotoolbox)[/bold green]"
            if vtb_check.passed
            else "[bold red]❌ Unavailable[/bold red]"
        )

        banner = (
            f"[bold cyan]🎬 slim-video[/bold cyan] [bold white]v{__version__}[/bold white]\n"
            f"[dim]Smart Apple Silicon Batch Video Transcoder with 20s Sample Estimation & TUI[/dim]\n\n"
            f"  • Author       : [cyan]{__author__}[/cyan]\n"
            f"  • Website      : [link={__url__}]{__url__}[/link]\n"
            f"  • GitHub       : [link={__github__}]{__github__}[/link]\n"
            f"  • Acceleration : {vtb_status}"
        )
        console.print(Panel(banner, title="✨ Version Info", border_style="cyan"))
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        "-V",
        help="Show version, acceleration status, and author info.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Global callback for global options."""


# ---------------------------------------------------------------------------
# Transcode Command (Main Workflow)
# ---------------------------------------------------------------------------


@app.command(
    "transcode",
    help="🚀 Scan a folder for H.264 videos, evaluate 20s samples, select, and transcode to HEVC.",
)
def cmd_transcode(
    path: Optional[str] = typer.Argument(
        None,
        help="Directory containing videos to process (default: interactive prompt or current folder).",
    ),
    min_gain: Optional[float] = typer.Option(
        None,
        "--min-gain",
        "-g",
        "-t",
        help="Minimum extrapolated gain % threshold (default: 10.0%).",
    ),
    quality: Optional[int] = typer.Option(
        None,
        "--quality",
        "-q",
        help="VideoToolbox quality factor (1=best, 100=smallest, default: 50).",
    ),
    sample_seconds: Optional[int] = typer.Option(
        None, "--sample-seconds", "-s", help="Sample test duration in seconds (default: 20s)."
    ),
    no_sample: bool = typer.Option(
        False, "--no-sample", help="Skip 20s mid-file sample estimation."
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Non-interactive mode (auto-transcode eligible files without confirmation prompts).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Simulate scan and estimation without creating files or modifying originals.",
    ),
    all_codecs: Optional[bool] = typer.Option(
        None, "--all-codecs", "-a", help="Scan all non-HEVC formats, not only H.264."
    ),
    delete_original: Optional[bool] = typer.Option(
        None,
        "--delete-original",
        "--delete",
        "-d",
        help="Permanently delete original video files after successful transcoding instead of moving to quarantine.",
    ),
) -> None:
    """Execute the core workflow: scan -> 20s sample test -> interactive tree -> transcode -> report."""
    missing = check_dependencies()
    if missing:
        console.print(
            Panel(
                f"[bold red]❌ Missing required dependencies: {', '.join(missing)}[/bold red]\n\n"
                "Please install ffmpeg with VideoToolbox support:\n"
                "  [bold cyan]brew install ffmpeg[/bold cyan]",
                title="⚠️ Missing Binaries",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    cfg = config_manager.load()
    active_quality = quality if quality is not None else cfg.quality
    active_min_gain = min_gain if min_gain is not None else cfg.min_gain_percent
    active_sample_sec = (
        sample_seconds if sample_seconds is not None else cfg.sample_duration_seconds
    )
    active_all_codecs = all_codecs if all_codecs is not None else cfg.all_codecs
    active_delete_original = delete_original if delete_original is not None else cfg.delete_original
    run_samples = not no_sample and cfg.auto_sample_test

    try:
        _run_main_workflow(
            path_arg=path,
            min_gain=active_min_gain,
            quality=active_quality,
            sample_seconds=active_sample_sec,
            run_samples=run_samples,
            yes=yes,
            dry_run=dry_run,
            all_codecs=active_all_codecs,
            delete_original=active_delete_original,
        )
    except KeyboardInterrupt:
        console.print(
            "\n[yellow]⚠️  Process cancelled by user (Ctrl+C). Exiting cleanly.[/yellow]\n"
        )
        raise typer.Exit(130) from None


# ---------------------------------------------------------------------------
# Estimate / Dry-Run Command
# ---------------------------------------------------------------------------


@app.command(
    "estimate",
    help="📊 Scan videos and run 20s sample estimation to preview savings WITHOUT transcoding.",
)
def cmd_estimate(
    path: Optional[str] = typer.Argument(
        None, help="Directory containing videos to evaluate (default: current folder)."
    ),
    min_gain: Optional[float] = typer.Option(
        None,
        "--min-gain",
        "-g",
        "-t",
        help="Minimum extrapolated gain % threshold (default: 10.0%).",
    ),
    quality: Optional[int] = typer.Option(
        None,
        "--quality",
        "-q",
        help="VideoToolbox quality factor (1=best, 100=smallest, default: 50).",
    ),
    sample_seconds: Optional[int] = typer.Option(
        None, "--sample-seconds", "-s", help="Sample test duration in seconds (default: 20s)."
    ),
    all_codecs: Optional[bool] = typer.Option(
        None, "--all-codecs", "-a", help="Scan all non-HEVC formats, not only H.264."
    ),
) -> None:
    """Run non-destructive scan and 20s test estimation, displaying a detailed breakdown table."""
    cmd_transcode(
        path=path,
        min_gain=min_gain,
        quality=quality,
        sample_seconds=sample_seconds,
        no_sample=False,
        yes=True,
        dry_run=True,
        all_codecs=all_codecs,
    )


# ---------------------------------------------------------------------------
# Core Workflow Implementation
# ---------------------------------------------------------------------------


def _prompt_interactive_folder_selection() -> str:
    """Display an interactive menu to choose folder or utility."""
    console.print(
        Panel.fit(
            f"[bold cyan]🎬 slim-video[/bold cyan] [dim]v{__version__}[/dim] ── "
            "[bold white]Smart Video Batch Transcoder[/bold white]\n"
            "[dim]Select an option or directory below to begin:[/dim]",
            border_style="cyan",
        )
    )

    cwd_path = os.getcwd()
    movies_path = str(Path.home() / "Movies")

    choices = [
        f"📁 Current Directory ({cwd_path})",
        "🔍 Enter Custom Directory Path…",
    ]
    if Path(movies_path).exists():
        choices.append(f"🏠 Movies Folder ({movies_path})")
    if Path("/Volumes").exists():
        volumes = [
            p for p in Path("/Volumes").iterdir() if p.is_dir() and not p.name.startswith(".")
        ]
        if volumes:
            choices.append("💾 Browse External Volumes (/Volumes)…")

    choices.extend(
        [
            "📊 Estimate Potential Space Savings (Dry Run)",
            "🩺 Run Hardware & System Diagnostics (Doctor)",
            "⚙️  Open Configuration Settings",
            "📈 View Lifetime Savings History",
            "🚪 Exit",
        ]
    )

    choice = inquirer.select(
        message="What would you like to do?",
        choices=choices,
        default=choices[0],
    ).execute()

    if choice.startswith("📁 Current Directory"):
        return cwd_path
    elif choice.startswith("🔍 Enter Custom"):
        selected_text = inquirer.text(
            message="Enter full folder path:",
            default=cwd_path,
        ).execute()
        return str(selected_text).strip()
    elif choice.startswith("🏠 Movies Folder"):
        return movies_path
    elif choice.startswith("💾 Browse External Volumes"):
        vol_choices = [str(p) for p in Path("/Volumes").iterdir() if p.is_dir()]
        selected_vol = inquirer.select(message="Select Volume:", choices=vol_choices).execute()
        return str(selected_vol)
    elif choice.startswith("📊 Estimate"):
        target = inquirer.text(message="Folder to estimate:", default=cwd_path).execute()
        cmd_estimate(path=target)
        sys.exit(0)
    elif choice.startswith("🩺 Run Hardware"):
        cmd_doctor(benchmark=True)
        sys.exit(0)
    elif choice.startswith("⚙️  Open Configuration"):
        cmd_config_wizard()
        sys.exit(0)
    elif choice.startswith("📈 View Lifetime"):
        cmd_history_stats()
        sys.exit(0)
    else:
        console.print("[dim]Goodbye![/dim]")
        sys.exit(0)


def _run_main_workflow(
    path_arg: Optional[str] = None,
    min_gain: float = 10.0,
    quality: int = DEFAULT_QUALITY,
    sample_seconds: int = SAMPLE_SECONDS,
    run_samples: bool = True,
    yes: bool = False,
    dry_run: bool = False,
    all_codecs: bool = False,
    delete_original: bool = False,
) -> None:
    """Execute the core workflow: scan -> sample evaluation -> interactive tree -> transcode -> report."""
    if not path_arg:
        if sys.stdin.isatty() and not yes:
            path_arg = _prompt_interactive_folder_selection()
        else:
            path_arg = os.getcwd()

    root = Path(path_arg).resolve()
    if not root.exists() or not root.is_dir():
        console.print(
            Panel(
                f"[bold red]❌ Directory not found:[/bold red] [yellow]{root}[/yellow]\n\n"
                "Please verify the path and ensure the folder exists.",
                title="⚠️ Invalid Folder",
                border_style="red",
            )
        )
        return

    mode_tag = "[bold yellow][DRY-RUN / ESTIMATION ONLY][/bold yellow] " if dry_run else ""
    console.print(
        Panel.fit(
            f"{mode_tag}[bold cyan]slim-video[/bold cyan] [dim]v{__version__}[/dim] ── "
            "[bold white]H.264 → x265 (HEVC) Auto Transcoder[/bold white]\n"
            f"[dim]Sample Test: {sample_seconds}s (mid-point) · Min Gain Threshold: {min_gain}% · Apple Silicon VideoToolbox[/dim]",
            border_style="yellow" if dry_run else "cyan",
        )
    )

    # 1. Scan files with animated spinner & real-time file discovery
    with console.status(
        f"[bold cyan]🔍 Scanning files in[/bold cyan] [yellow]{root.name}/[/yellow]…",
        spinner="dots",
    ) as scan_status:

        def _scan_progress(cur_file: Path, cand_count: int, hevc_count: int) -> None:
            disp_name = format_file_label(cur_file.name, extra_width_needed=45)
            scan_status.update(
                f"[bold cyan]🔍 Scanning directory…[/bold cyan] [yellow]{disp_name}[/yellow] "
                f"[dim]({cand_count} candidates, {hevc_count} HEVC found)[/dim]"
            )

        candidates, already_hevc = find_h264_candidates(
            root, all_codecs=all_codecs, progress_callback=_scan_progress
        )

    if already_hevc:
        console.print(
            f"[green]✓  {len(already_hevc)} video file(s) already encoded in HEVC/x265 (skipped).[/green]"
        )

    if not candidates:
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

                    history.record_test(
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

    if below_thresh_count > 0:
        console.print(
            f"[dim]ℹ️  {below_thresh_count} file(s) had an estimated gain < {min_gain}% and were automatically unchecked.[/dim]"
        )

    # 3. Dry-Run Table display if estimate-only requested
    if dry_run:
        _display_estimation_table(root=root, items=file_items, min_gain=min_gain)
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

    console.print(
        Panel(
            f"[bold green]Ready to transcode {len(selected_items)} file(s) to x265 (HEVC)[/bold green]\n\n"
            f"  • Source Total Size     : [bold]{fmt_bytes(total_selected_size)}[/bold]\n"
            f"  • Projected HEVC Size   : [bold]{fmt_bytes(total_selected_est)}[/bold] "
            f"([bold green]Est. Saved: {fmt_bytes(est_saving)} / -{est_pct}%[/bold green])\n"
            f"  • Video Encoder         : VideoToolbox 10-bit HEVC (Quality: {quality})\n"
            f"  • Audio / Subtitles     : Stream Copied (100% Lossless)\n"
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
    _execute_batch(
        root=root,
        items=selected_items,
        total_scanned=len(file_items),
        quality=quality,
        delete_original=delete_original,
    )


# ---------------------------------------------------------------------------
# Estimation Table Display
# ---------------------------------------------------------------------------


def _display_estimation_table(root: Path, items: list[FileItem], min_gain: float) -> None:
    """Print an estimation summary table for dry-run inspection."""
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

    total_orig = 0
    total_est = 0
    eligible_count = 0

    for it in items:
        total_orig += it.size
        est = it.estimated_size if it.estimated_size is not None else it.size
        total_est += est

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

    saved = max(total_orig - total_est, 0)
    pct = round((saved / total_orig) * 100, 1) if total_orig else 0.0

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


# ---------------------------------------------------------------------------
# Batch Execution & Reporting
# ---------------------------------------------------------------------------


def _execute_batch(
    root: Path,
    items: list[FileItem],
    total_scanned: int,
    quality: int,
    delete_original: bool = False,
) -> None:
    """Execute batch transcoding, display progress, and write text report."""
    console.print(
        f"\n[bold green]🚀  Starting batch transcoding for {len(items)} file(s)…[/bold green]\n"
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
                delete_original=delete_original,
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

                history.record_transcode(
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
                    status="error",
                    error_message=result.get("error"),
                )
                summary.total_files_failed += 1
                summary.records.append(record)

                history.record_transcode(
                    file_path=str(item.path),
                    codec=item.codec,
                    original_size=orig_size,
                    final_size=0,
                    gain_pct=0.0,
                    status="error",
                    quality=quality,
                )

            progress.advance(batch_task)

    total_batch_sec = max(time.perf_counter() - start_perf, 0.1)
    summary.total_duration_sec = total_batch_sec
    summary.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if summary.total_original_bytes > 0:
        summary.total_gain_pct = round(
            (summary.total_saved_bytes / summary.total_original_bytes) * 100, 1
        )

    report_path = save_report_file(summary.directory, summary)

    _display_batch_summary(summary, report_path)


def _display_batch_summary(summary: BatchSummary, report_path: Path) -> None:
    """Print the final batch summary panel and detailed breakdown."""
    console.print("")

    action_line = (
        "  • Original Files Action: [bold red]Permanently Deleted (Direct Deletion Mode)[/bold red]\n"
        if summary.delete_original
        else f"  • Quarantine Subfolder : [cyan]{summary.directory / '_originals_to_delete'}[/cyan]\n"
    )

    console.print(
        Panel(
            f"[bold green]Batch Transcoding Complete in {fmt_duration(summary.total_duration_sec)}![/bold green]\n\n"
            f"  • Successful Files     : [bold green]{summary.total_files_successful}/{summary.total_files_selected}[/bold green]\n"
            f"  • Failed Files         : [bold red]{summary.total_files_failed}[/bold red]\n"
            f"  • Original Size        : [bold]{fmt_bytes(summary.total_original_bytes)}[/bold]\n"
            f"  • New HEVC Size        : [bold]{fmt_bytes(summary.total_final_bytes)}[/bold]\n"
            f"  • Disk Space Freed     : [bold green]{fmt_bytes(summary.total_saved_bytes)}[/bold green] "
            f"([bold green]-{summary.total_gain_pct}%[/bold green])\n"
            f"{action_line}"
            f"  • Text Report Saved    : [bold cyan]{report_path}[/bold cyan]",
            title="🎉  Summary & Results",
            border_style="green",
        )
    )

    t = Table(title="📋  Transcode Breakdown", expand=True, border_style="cyan")
    t.add_column("File", style="cyan", no_wrap=False, overflow="fold")
    t.add_column("Original", justify="right")
    t.add_column("HEVC", justify="right")
    t.add_column("Saved", justify="right", style="green")
    t.add_column("Gain", justify="right", style="bold green")
    t.add_column("Speed", justify="center", style="yellow")
    t.add_column("Status", justify="center")

    for r in summary.records:
        status_badge = "[green]✅ OK[/green]" if r.status == "ok" else "[red]❌ Error[/red]"
        t.add_row(
            r.rel_path,
            fmt_bytes(r.original_size),
            fmt_bytes(r.final_size) if r.status == "ok" else "—",
            fmt_bytes(r.saved_bytes) if r.status == "ok" else "—",
            f"-{r.gain_pct}%" if r.status == "ok" else "—",
            r.speed,
            status_badge,
        )

    console.print(t)
    if summary.delete_original:
        console.print(
            "\n[bold green]✓ Original H.264 video files were permanently deleted as requested.[/bold green]\n"
        )
    else:
        console.print(
            "\n[dim]Original H.264 videos are safely moved in [cyan]_originals_to_delete/[/cyan]. "
            "Review your new HEVC files and delete the quarantine folder when satisfied.[/dim]\n"
        )


# ---------------------------------------------------------------------------
# Doctor Diagnostics Command
# ---------------------------------------------------------------------------


@app.command(
    "doctor",
    help="🩺 Run environment and hardware diagnostic checks (VideoToolbox acceleration, temp storage).",
)
def cmd_doctor(
    benchmark: bool = typer.Option(
        True,
        "--benchmark/--no-benchmark",
        help="Run a live 1-second synthetic hardware transcode benchmark.",
    ),
) -> None:
    """Run full system diagnostic and hardware verification."""
    console.print(
        Panel.fit(
            "[bold cyan]slim-video Doctor[/bold cyan] ── [bold white]System & Hardware Diagnostics[/bold white]\n"
            "[dim]Verifies ffmpeg, ffprobe, VideoToolbox hardware acceleration, and environment health[/dim]",
            border_style="cyan",
        )
    )

    with console.status("[bold cyan]Running diagnostic checks…[/bold cyan]"):
        results = run_all_doctor_checks(include_benchmark=benchmark)

    table = Table(title="🏥 Diagnostic Results", expand=True)
    table.add_column("Status", justify="center", width=8)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Details", style="dim")

    all_passed = True
    for r in results:
        if r.passed:
            status_str = "[bold green]✅ PASS[/bold green]"
        elif not r.critical:
            status_str = "[bold yellow]⚠️ WARN[/bold yellow]"
        else:
            status_str = "[bold red]❌ FAIL[/bold red]"
            all_passed = False
        table.add_row(status_str, r.name, r.details)

    console.print(table)
    console.print("")

    if all_passed:
        console.print(
            Panel(
                "[bold green]🚀 All checks passed![/bold green]\n\n"
                "Your system is correctly configured and ready to run hardware-accelerated HEVC transcoding.\n"
                "You can now run: [bold cyan]slim-video /path/to/videos[/bold cyan]",
                title="✨ Ready to Transcode",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[bold red]❌ Environment issues detected.[/bold red]\n\n"
                "Please fix the failing items above before transcoding.\n"
                "Run with [bold]brew install ffmpeg[/bold] if tools are missing.",
                title="⚠️ Diagnostics Incomplete",
                border_style="red",
            )
        )
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Configuration Commands & Wizard
# ---------------------------------------------------------------------------

config_app = typer.Typer(
    name="config",
    help="⚙️  Manage application configuration settings.",
    no_args_is_help=False,
)
app.add_typer(config_app, name="config")


@config_app.callback(invoke_without_command=True)
def config_default(ctx: typer.Context) -> None:
    """Show configuration if no subcommand given."""
    if ctx.invoked_subcommand is None:
        cmd_config_show()


@config_app.command("show", help="📋 Display all current settings in a formatted table.")
def cmd_config_show() -> None:
    """Display current configuration in a table."""
    cfg = config_manager.load()
    table = Table(title="⚙️  slim-video Configuration Settings", expand=True)
    table.add_column("Setting Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="bold green")
    table.add_column("Description", style="dim")

    descriptions = {
        "min_gain_percent": "Minimum extrapolated gain % to select by default (< threshold = unchecked)",
        "sample_duration_seconds": "Duration of test encode sample taken from the middle (seconds)",
        "quality": "VideoToolbox HEVC quality factor (1=best, 100=smallest)",
        "auto_sample_test": "Whether to run automatic 20s sample tests on candidates",
        "quarantine_dir": "Subdirectory name where originals are moved after transcoding",
        "all_codecs": "Whether to process all non-HEVC video formats or only H.264",
        "encoder": "FFmpeg HEVC video encoder (default: hevc_videotoolbox)",
    }

    for k, v in cfg.model_dump().items():
        desc = descriptions.get(k, "")
        table.add_row(k, str(v), desc)

    console.print(table)
    console.print(f"[dim]Config file path: {config_manager.config_path}[/dim]\n")


@config_app.command(
    "set",
    help="✏️  Update a configuration setting (e.g. `slim-video config set min_gain_percent 15`).",
)
def cmd_config_set(
    key: str = typer.Argument(..., help="Setting key name to change."),
    value: str = typer.Argument(..., help="New value for the setting."),
) -> None:
    """Update a specific setting."""
    try:
        k, new_val = config_manager.set(key, value)
        console.print(f"[bold green]✓  Updated '{k}' to {new_val}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]✗  Error updating '{key}': {e}[/bold red]")
        raise typer.Exit(1) from None


@config_app.command("get", help="🔍 Get the current value of a configuration setting.")
def cmd_config_get(
    key: str = typer.Argument(..., help="Setting key name to inspect."),
) -> None:
    """Get the value of a single setting."""
    try:
        val = config_manager.get(key)
        console.print(f"[cyan]{key}[/cyan] = [bold green]{val}[/bold green]")
    except KeyError as e:
        console.print(f"[bold red]✗  {e}[/bold red]")
        raise typer.Exit(1) from None


@config_app.command("reset", help="🔄 Reset all settings to factory default values.")
def cmd_config_reset() -> None:
    """Reset configuration to defaults."""
    config_manager.reset()
    console.print("[bold green]✓  Configuration reset to default settings.[/bold green]")
    cmd_config_show()


@config_app.command("path", help="📁 Print the absolute path of the configuration file.")
def cmd_config_path() -> None:
    """Print configuration file location."""
    console.print(f"[dim]Config file path:[/dim] [cyan]{config_manager.config_path}[/cyan]")


@config_app.command("wizard", help="🧙 Interactive step-by-step configuration wizard.")
def cmd_config_wizard() -> None:
    """Guide user through updating all settings interactively."""
    cfg = config_manager.load()
    console.print(
        Panel(
            "[bold cyan]🧙 slim-video Configuration Wizard[/bold cyan]\n"
            "[dim]Press Enter to accept current value or type a new one:[/dim]",
            border_style="cyan",
        )
    )

    try:
        new_gain = inquirer.text(
            message="Minimum gain % threshold to transcode by default:",
            default=str(cfg.min_gain_percent),
        ).execute()

        new_duration = inquirer.text(
            message="Sample test duration in seconds (taken from middle):",
            default=str(cfg.sample_duration_seconds),
        ).execute()

        new_quality = inquirer.text(
            message="VideoToolbox quality factor (1=best quality, 100=smallest):",
            default=str(cfg.quality),
        ).execute()

        new_auto_sample = inquirer.confirm(
            message="Run automatic 20s sample tests on video candidates?",
            default=cfg.auto_sample_test,
        ).execute()

        new_quarantine = inquirer.text(
            message="Quarantine subfolder name for originals:",
            default=cfg.quarantine_dir,
        ).execute()

        new_delete_original = inquirer.confirm(
            message="Permanently delete original files after transcoding (instead of moving to quarantine)?",
            default=cfg.delete_original,
        ).execute()

        config_manager.set("min_gain_percent", new_gain)
        config_manager.set("sample_duration_seconds", new_duration)
        config_manager.set("quality", new_quality)
        config_manager.set("auto_sample_test", str(new_auto_sample))
        config_manager.set("quarantine_dir", new_quarantine)
        config_manager.set("delete_original", str(new_delete_original))

        console.print("\n[bold green]✅ All settings updated successfully![/bold green]\n")
        cmd_config_show()
    except Exception as e:
        console.print(f"\n[bold red]✗  Wizard failed: {e}[/bold red]")
        raise typer.Exit(1) from None


# ---------------------------------------------------------------------------
# History & Lifetime Savings Commands
# ---------------------------------------------------------------------------

history_app = typer.Typer(
    name="history",
    help="📊  Inspect cumulative disk space savings and past transcode history.",
    no_args_is_help=False,
)
app.add_typer(history_app, name="history")


@history_app.callback(invoke_without_command=True)
def history_default(ctx: typer.Context) -> None:
    """Show cumulative statistics if no subcommand given."""
    if ctx.invoked_subcommand is None:
        cmd_history_stats()


@history_app.command("stats", help="📊 Display lifetime cumulative disk space saved.")
def cmd_history_stats() -> None:
    """Show overall stats and recent entries."""
    if not history.path.exists():
        console.print("[dim]No history recorded yet.[/dim]\n")
        return

    stats = history.get_stats()
    console.print(
        Panel(
            f"Total Transcodes Completed : [bold green]{stats['successful_transcodes']}/{stats['total_transcodes']}[/bold green]\n"
            f"Total Original Volume      : [bold]{fmt_bytes(stats['original_bytes'])}[/bold]\n"
            f"Total HEVC Volume          : [bold]{fmt_bytes(stats['final_bytes'])}[/bold]\n"
            f"Total Storage Freed        : [bold green]{fmt_bytes(stats['saved_bytes'])}[/bold green] "
            f"([bold green]-{stats['overall_gain_pct']}%[/bold green])",
            title="📊  Lifetime Storage Savings",
            border_style="magenta",
        )
    )

    data = history.get_all()
    transcodes = data.get("transcodes", [])
    if transcodes:
        t = Table(title="🎬  Recent Transcodes (Latest 10)", expand=True)
        for col, style in [
            ("Date", "dim"),
            ("File", "cyan"),
            ("Codec", "magenta"),
            ("Original", ""),
            ("HEVC", ""),
            ("Gain", "green"),
            ("Status", ""),
        ]:
            t.add_column(
                col,
                style=style,
                justify="right" if col in ("Original", "HEVC", "Gain") else "left",
                no_wrap=False if col == "File" else True,
                overflow="fold" if col == "File" else "ellipsis",
            )
        for entry in reversed(transcodes[-10:]):
            status_str = "[green]OK[/green]" if entry.get("status") == "ok" else "[red]Error[/red]"
            t.add_row(
                entry.get("timestamp", ""),
                entry.get("name", ""),
                entry.get("codec", ""),
                fmt_bytes(entry.get("original_size", 0)),
                fmt_bytes(entry.get("final_size", 0)),
                f"-{entry.get('gain_pct', 0)}%" if entry.get("status") == "ok" else "—",
                status_str,
            )
        console.print(t)
    else:
        console.print("[dim]No individual transcodes recorded yet.[/dim]\n")


@history_app.command("clear", help="🗑️  Reset lifetime history store.")
def cmd_history_clear() -> None:
    """Clear history file."""
    history.clear()
    console.print("[bold green]✓  History data cleared successfully.[/bold green]")


# ---------------------------------------------------------------------------
# Direct Main Entrypoint with Smart Default Dispatch
# ---------------------------------------------------------------------------


def main(args: Optional[list[str]] = None) -> None:
    """Main CLI entrypoint with smart subcommand dispatching and signal handling."""
    argv = list(sys.argv[1:] if args is None else args)

    known_subcommands = {
        "transcode",
        "estimate",
        "doctor",
        "config",
        "history",
        "--help",
        "-h",
        "--version",
        "-v",
        "-V",
    }

    try:
        if (
            not argv
            or (argv and argv[0] in known_subcommands)
            or (argv and argv[0].startswith("-"))
        ):
            app(argv)
        else:
            # First argument is a path -> treat as transcode command
            argv.insert(0, "transcode")
            app(argv)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Process cancelled by user. Exiting cleanly.[/yellow]\n")
        sys.exit(130)


if __name__ == "__main__":
    main()
