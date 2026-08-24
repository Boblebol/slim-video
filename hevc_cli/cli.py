"""hevc-cli — Simplified H.264 to HEVC/x265 batch transcoder for Apple Silicon.

Features:
- Scans directory recursively for H.264/AVC videos
- Evaluates candidate files with a real 20-second sample encode in the middle
- Automatically flags and deselects files with < 10% extrapolated gain ("ça ne vaut pas le coup")
- Interactive collapsible Tree View with checkboxes to fold/unfold & select files
- Automatic hardware-accelerated x265 compression preserving source quality
- Lossless copy of all audio tracks and subtitles
- Detailed summary text report of disk space gained
- Persistent and explicit configuration file manageable via `hevc-cli config`
- Built-in environment & hardware diagnostics via `hevc-cli doctor`
- Safe quarantine of original files (never permanently deletes without user consent)
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

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

from hevc_cli import __version__
from hevc_cli.config import config_manager
from hevc_cli.core import (
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
from hevc_cli.doctor import run_all_doctor_checks
from hevc_cli.history import HistoryManager
from hevc_cli.models import BatchSummary, FileItem, TranscodeRecord
from hevc_cli.report import save_report_file
from hevc_cli.tree_selector import fmt_bytes, fmt_duration, select_files_interactive

# ---------------------------------------------------------------------------
# App Bootstrap
# ---------------------------------------------------------------------------

console = Console()
app = typer.Typer(
    name="hevc-cli",
    help="🎬  Simplified H.264 to x265/HEVC batch transcoder for Apple Silicon.",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=False,
)
history = HistoryManager()


# ---------------------------------------------------------------------------
# Transcode Command (Default)
# ---------------------------------------------------------------------------


@app.command(
    "transcode",
    help="Scan a directory for H.264 videos, evaluate 20s samples, select, and transcode.",
)
def cmd_transcode(
    path: str | None = typer.Argument(
        None, help="Directory containing videos to process (default: current folder)."
    ),
    min_gain: float | None = typer.Option(
        None, "--min-gain", "-g", help="Minimum extrapolated gain % threshold (default: 10.0%)."
    ),
    quality: int | None = typer.Option(
        None, "--quality", "-q", help="VideoToolbox quality factor (1=best, 100=smallest)."
    ),
    sample_seconds: int | None = typer.Option(
        None, "--sample-seconds", "-s", help="Sample test duration in seconds (default: 20s)."
    ),
    no_sample: bool = typer.Option(
        False, "--no-sample", help="Skip 20s mid-file sample estimation."
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Non-interactive mode (auto-transcode eligible files without prompts).",
    ),
    all_codecs: bool | None = typer.Option(
        None, "--all-codecs", "-a", help="Scan all non-HEVC formats, not only H.264."
    ),
) -> None:
    """Execute the core workflow: scan -> 20s sample test -> interactive tree -> transcode -> report."""
    missing = check_dependencies()
    if missing:
        console.print(
            f"[bold red]✗  Missing required dependencies: {', '.join(missing)}[/bold red]\n"
            "  Install with: [bold]brew install ffmpeg[/bold]"
        )
        raise typer.Exit(1)

    cfg = config_manager.load()
    active_quality = quality if quality is not None else cfg.quality
    active_min_gain = min_gain if min_gain is not None else cfg.min_gain_percent
    active_sample_sec = (
        sample_seconds if sample_seconds is not None else cfg.sample_duration_seconds
    )
    active_all_codecs = all_codecs if all_codecs is not None else cfg.all_codecs
    run_samples = not no_sample and cfg.auto_sample_test

    _run_main_workflow(
        path_arg=path,
        min_gain=active_min_gain,
        quality=active_quality,
        sample_seconds=active_sample_sec,
        run_samples=run_samples,
        yes=yes,
        all_codecs=active_all_codecs,
    )


def _run_main_workflow(
    path_arg: str | None = None,
    min_gain: float = 10.0,
    quality: int = DEFAULT_QUALITY,
    sample_seconds: int = SAMPLE_SECONDS,
    run_samples: bool = True,
    yes: bool = False,
    all_codecs: bool = False,
) -> None:
    """Execute the core workflow: scan -> sample evaluation -> interactive tree -> transcode -> report."""
    console.print(
        Panel.fit(
            f"[bold cyan]hevc-cli[/bold cyan] [dim]v{__version__}[/dim] ── "
            "[bold white]H.264 → x265 (HEVC) Auto Transcoder[/bold white]\n"
            f"[dim]Sample Test: {sample_seconds}s (milieu) · Seuil gain min: {min_gain}% · Apple Silicon VideoToolbox[/dim]",
            border_style="cyan",
        )
    )

    # 1. Ask or resolve path
    if not path_arg:
        if not sys.stdin.isatty() or yes:
            path_arg = os.getcwd()
        else:
            path_arg = inquirer.text(
                message="Folder to scan and transcode:",
                default=os.getcwd(),
            ).execute()

    root = Path(path_arg).resolve()
    if not root.exists() or not root.is_dir():
        console.print(f"[bold red]✗  Folder not found: {root}[/bold red]")
        return

    # 2. Scan files
    console.print(f"\n[bold cyan]🔍  Scanning[/bold cyan] [yellow]{root}[/yellow]...")
    candidates, already_hevc = find_h264_candidates(root, all_codecs=all_codecs)

    if already_hevc:
        console.print(
            f"[green]✓  {len(already_hevc)} video file(s) already encoded in HEVC/x265 (skipped).[/green]"
        )

    if not candidates:
        if already_hevc:
            console.print(
                "[bold green]🎉  All video files in this folder are already optimized in HEVC![/bold green]\n"
            )
        else:
            console.print("[yellow]No H.264 video files found in this folder.[/yellow]\n")
        return

    # 3. Probe metadata & run 20s middle sample evaluation
    console.print(
        f"[bold blue]🧪  Evaluating {len(candidates)} candidate file(s) "
        f"({sample_seconds}s sample test at mid-point)...[/bold blue]"
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

            progress.update(task, description=f"Analyzing [cyan]{f.name[:28]}[/cyan]…")

            codec = get_video_codec(f) or "h264"
            res = get_resolution(f)
            fps = get_fps(f)
            dur = get_duration(f)
            audio = get_audio_summary(f)
            size = f.stat().st_size if f.exists() else 0

            est_size: int | None = None
            est_gain: float | None = None
            below_thresh = False
            selected = True

            if run_samples and size > 0:

                def _sample_cb(pct: float, _elapsed: float, speed: str, _f: Path = f) -> None:
                    progress.update(
                        task, description=f"Sample 20s [cyan]{_f.name[:28]}[/cyan] ({pct:.0f}%)"
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
            f"[dim]ℹ️  {below_thresh_count} file(s) have estimated gain < {min_gain}% and were unchecked by default.[/dim]"
        )

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
        console.print("[yellow]No files selected. Aborted.[/yellow]\n")
        return

    # 5. Pre-transcode summary
    total_selected_size = sum(item.size for item in selected_items)
    total_selected_est = sum(
        (item.estimated_size if item.estimated_size is not None else item.size)
        for item in selected_items
    )
    est_saving = max(total_selected_size - total_selected_est, 0)
    est_pct = round((est_saving / total_selected_size) * 100, 1) if total_selected_size else 0.0

    console.print(
        Panel(
            f"[bold green]Ready to transcode {len(selected_items)} file(s) to x265 (HEVC)[/bold green]\n\n"
            f"  • Source Total Size     : [bold]{fmt_bytes(total_selected_size)}[/bold]\n"
            f"  • Projected HEVC Size   : [bold]{fmt_bytes(total_selected_est)}[/bold] "
            f"([bold green]Est. Saved: {fmt_bytes(est_saving)} / -{est_pct}%[/bold green])\n"
            f"  • Video Settings        : VideoToolbox 10-bit HEVC (Quality factor: {quality})\n"
            f"  • Audio / Subtitles     : Stream Copied (100% Lossless)\n"
            f"  • Original Safety       : Moved to [cyan]{root / '_originals_to_delete'}[/cyan]\n"
            f"  • Space Summary Report  : Will be saved to [cyan]{root / 'transcode_report.txt'}[/cyan]",
            title="📋  Transcode Summary",
            border_style="green",
        )
    )

    if not yes:
        confirmed = inquirer.confirm(
            message=f"Start transcoding {len(selected_items)} file(s)?",
            default=True,
        ).execute()
        if not confirmed:
            console.print("[yellow]Aborted by user.[/yellow]\n")
            return

    # 6. Run Transcoding
    _execute_batch(
        root=root,
        items=selected_items,
        total_scanned=len(file_items),
        quality=quality,
    )


# ---------------------------------------------------------------------------
# Batch Execution & Reporting
# ---------------------------------------------------------------------------


def _execute_batch(
    root: Path,
    items: list[FileItem],
    total_scanned: int,
    quality: int,
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
                progress.update(
                    file_task,
                    completed=pct,
                    description=(
                        f"[bold cyan]{_f.name[:32]}[/bold cyan] "
                        f"[green]{pct:.1f}%[/green] "
                        f"{fmt_duration(elapsed)}/{fmt_duration(_dur)} "
                        f"@ [yellow]{speed}[/yellow]"
                    ),
                )

            progress.update(
                file_task,
                completed=0,
                description=f"[bold cyan]{f.name[:32]}[/bold cyan] — starting…",
            )

            result = transcode(
                src=f,
                library_root=root,
                quality=quality,
                progress_callback=_progress_cb,
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
                    status="ok",
                )
                summary.total_files_successful += 1
                summary.total_original_bytes += orig_size
                summary.total_final_bytes += final_size
                summary.total_saved_bytes += saved

                history.record_transcode(
                    file_path=str(f),
                    codec=item.codec,
                    original_size=orig_size,
                    final_size=final_size,
                    gain_pct=gain,
                    quality=quality,
                    status="ok",
                )

                console.print(
                    f"  [bold green]✓[/bold green] {item.rel_path} → HEVC "
                    f"({fmt_bytes(orig_size)} → [bold]{fmt_bytes(final_size)}[/bold], "
                    f"[bold green]-{gain}%[/bold green])"
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
                    speed=last_speed[0],
                    status="error",
                    error_message=result.get("error_message") or "Transcoding failed",
                )
                summary.total_files_failed += 1
                summary.total_original_bytes += orig_size

                history.record_transcode(
                    file_path=str(f),
                    codec=item.codec,
                    original_size=orig_size,
                    final_size=0,
                    gain_pct=0.0,
                    quality=quality,
                    status="error",
                )

                console.print(f"  [bold red]✗  Failed: {item.rel_path}[/bold red]")

            summary.records.append(record)
            progress.advance(batch_task)

    # Final statistics calculation
    summary.total_duration_sec = time.perf_counter() - start_perf
    summary.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if summary.total_original_bytes > 0:
        summary.total_gain_pct = round(
            (summary.total_saved_bytes / summary.total_original_bytes) * 100, 1
        )

    # 7. Write Text Report
    report_file = save_report_file(root, summary)

    # 8. Print Results Panel
    console.print("")
    console.print(
        Panel(
            f"[bold green]Batch Transcoding Complete![/bold green]\n\n"
            f"  • Files Transcoded     : [bold]{summary.total_files_successful}/{len(items)}[/bold] successful\n"
            f"  • Original Total Size  : [bold]{fmt_bytes(summary.total_original_bytes)}[/bold]\n"
            f"  • New HEVC Total Size  : [bold]{fmt_bytes(summary.total_final_bytes)}[/bold]\n"
            f"  • Storage Freed        : [bold green]{fmt_bytes(summary.total_saved_bytes)}[/bold green] "
            f"([bold green]-{summary.total_gain_pct}%[/bold green])\n"
            f"  • Total Time Taken     : {fmt_duration(summary.total_duration_sec)}\n\n"
            f"📄 [bold cyan]Detailed Report saved to:[/bold cyan]\n"
            f"   [yellow]{report_file}[/yellow]\n\n"
            f"📦 [bold cyan]Original H.264 files moved to:[/bold cyan]\n"
            f"   [yellow]{root / '_originals_to_delete'}[/yellow]\n"
            f"   [dim](Check video playback, then delete this folder to permanently reclaim disk space)[/dim]",
            title="🎉  Summary & Results",
            border_style="green",
        )
    )


# ---------------------------------------------------------------------------
# Doctor Command (System Health & Hardware Validation)
# ---------------------------------------------------------------------------


@app.command(
    "doctor",
    help="Check system environment, ffmpeg installation, and test Apple VideoToolbox hardware acceleration.",
)
def cmd_doctor(
    benchmark: bool = typer.Option(
        True,
        "--benchmark/--no-benchmark",
        help="Run a real 1-second synthetic hardware transcode test.",
    ),
) -> None:
    """Run full system diagnostic and hardware verification."""
    console.print(
        Panel.fit(
            "[bold cyan]hevc-cli Doctor[/bold cyan] ── [bold white]System & Hardware Diagnostics[/bold white]\n"
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
                "You can now run: [bold cyan]hevc-cli /path/to/videos[/bold cyan]",
                title="✨ Ready to Transcode",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[bold red]❌ Environment issues detected.[/bold red]\n\n"
                "Please fix the failing items above before transcoding.\n"
                "Most issues can be solved by running: [bold]brew install ffmpeg[/bold]",
                title="⚠️ Attention Required",
                border_style="red",
            )
        )
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Config Management Command Group
# ---------------------------------------------------------------------------

config_app = typer.Typer(
    name="config",
    help="⚙️  Manage explicit configuration settings (~/.hevc_cli_config.json).",
    no_args_is_help=False,
)
app.add_typer(config_app, name="config")


@config_app.callback(invoke_without_command=True)
def cmd_config_default(ctx: typer.Context) -> None:
    """Show current configuration when no subcommand is specified."""
    if ctx.invoked_subcommand is None:
        cmd_config_show()


@config_app.command("show", help="Display all current settings.")
def cmd_config_show() -> None:
    """Display current configuration in a table."""
    cfg = config_manager.load()
    table = Table(title="⚙️  hevc-cli Configuration Settings", expand=True)
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
    "set", help="Update a configuration setting (e.g. `hevc-cli config set min_gain_percent 15`)."
)
def cmd_config_set(
    key: str = typer.Argument(..., help="Setting key name to change."),
    value: str = typer.Argument(..., help="New value for the setting."),
) -> None:
    """Update a specific setting."""
    try:
        k, new_val = config_manager.set(key, value)
        console.print(f"[bold green]✓  Updated '{k}' to {new_val}[/bold green]")
    except KeyError as exc:
        console.print(f"[bold red]✗  {exc}[/bold red]")
    except ValueError as exc:
        console.print(f"[bold red]✗  Invalid value format: {exc}[/bold red]")


@config_app.command("reset", help="Reset all settings to default values.")
def cmd_config_reset() -> None:
    """Reset configuration to defaults."""
    if inquirer.confirm(message="Reset all settings to defaults?", default=False).execute():
        config_manager.reset()
        console.print("[green]Configuration reset to defaults.[/green]")


@config_app.command("path", help="Print configuration file path.")
def cmd_config_path() -> None:
    """Print configuration file path."""
    console.print(str(config_manager.config_path))


# ---------------------------------------------------------------------------
# History Subcommand
# ---------------------------------------------------------------------------


@app.command("history", help="Display cumulative storage savings and transcoding history.")
def cmd_history(
    action: str = typer.Option("view", "--action", "-a", help="Action: view | clear"),
) -> None:
    """Display cumulative storage savings and transcoding history."""
    if action == "clear":
        if inquirer.confirm(message="Clear all history permanently?", default=False).execute():
            history.clear()
            console.print("[green]History cleared.[/green]")
        return

    stats = history.get_stats()
    console.print(
        Panel(
            f"Total Transcodes Completed : [bold green]{stats['successful_transcodes']}/{stats['total_transcodes']}[/bold green]\n"
            f"Total Original Volume      : [bold]{fmt_bytes(stats['original_bytes'])}[/bold]\n"
            f"Total HEVC Volume          : [bold]{fmt_bytes(stats['final_bytes'])}[/bold]\n"
            f"Total Storage Freed        : [bold green]{fmt_bytes(stats['saved_bytes'])}[/bold green] "
            f"([bold green]-{stats['overall_gain_pct']}%[/bold green])",
            title="📊  Cumulative Storage Savings",
            border_style="magenta",
        )
    )

    data = history.get_all()
    transcodes = data.get("transcodes", [])
    if transcodes:
        t = Table(title="🎬  Recent Transcodes (Latest 15)", expand=True)
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
            )
        for entry in reversed(transcodes[-15:]):
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
        console.print("[dim]No transcodes recorded yet.[/dim]\n")


# ---------------------------------------------------------------------------
# Direct Main Entrypoint with Smart Default Dispatch
# ---------------------------------------------------------------------------


def main(args: list[str] | None = None) -> None:
    """Main CLI entrypoint with smart subcommand dispatching."""
    argv = list(sys.argv[1:] if args is None else args)

    known_subcommands = {"doctor", "config", "history", "--help", "-h", "--version", "-v"}
    if (
        not argv
        or (
            argv
            and argv[0] not in known_subcommands
            and not argv[0].startswith("-")
            and argv[0] == "transcode"
        )
        or argv
        and argv[0] in known_subcommands
    ):
        app(argv)
    else:
        # Default to transcode command
        argv.insert(0, "transcode")
        app(argv)


if __name__ == "__main__":
    main()
