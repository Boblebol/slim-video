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

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from slim_video import __author__, __github__, __url__, __version__
from slim_video.config import config_manager
from slim_video.core import (
    check_dependencies,
    find_h264_candidates,
)
from slim_video.doctor import check_videotoolbox_support, run_all_doctor_checks
from slim_video.formatting import fmt_bytes
from slim_video.history import HistoryManager
from slim_video.ui.prompts import (
    prompt_interactive_folder_selection,
    run_config_wizard,
)
from slim_video.workflow import (
    display_estimation_table,
    execute_batch,
    run_main_workflow,
)

# ---------------------------------------------------------------------------
# App Bootstrap & Styling
# ---------------------------------------------------------------------------

console = Console()


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
    ssd_staging: Optional[bool] = typer.Option(
        None,
        "--ssd-staging",
        help="Use fast SSD staging (/tmp/slim-video) to eliminate head-thrashing on external mechanical HDDs.",
    ),
    temp_dir: Optional[str] = typer.Option(
        None,
        "--temp-dir",
        help="Custom temporary SSD directory for staging (requires --ssd-staging).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON format for scripting and automation.",
    ),
) -> None:
    """Execute the core workflow: scan -> 20s sample test -> interactive tree -> transcode -> report."""
    missing = check_dependencies()
    if missing:
        if json_output:
            import json

            print(json.dumps({"error": f"Missing required dependencies: {', '.join(missing)}"}))
            raise typer.Exit(1)
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
    active_quality = (
        quality
        if quality is not None and not isinstance(quality, typer.models.OptionInfo)
        else cfg.quality
    )
    active_min_gain = (
        min_gain
        if min_gain is not None and not isinstance(min_gain, typer.models.OptionInfo)
        else cfg.min_gain_percent
    )
    active_sample_sec = (
        sample_seconds
        if sample_seconds is not None and not isinstance(sample_seconds, typer.models.OptionInfo)
        else cfg.sample_duration_seconds
    )
    active_all_codecs = (
        all_codecs
        if all_codecs is not None and not isinstance(all_codecs, typer.models.OptionInfo)
        else cfg.all_codecs
    )
    active_delete_original = (
        delete_original
        if delete_original is not None and not isinstance(delete_original, typer.models.OptionInfo)
        else cfg.delete_original
    )
    active_ssd_staging = (
        ssd_staging
        if ssd_staging is not None and not isinstance(ssd_staging, typer.models.OptionInfo)
        else cfg.ssd_staging
    )
    run_samples = not no_sample and cfg.auto_sample_test

    temp_dir_val = (
        temp_dir
        if temp_dir is not None and not isinstance(temp_dir, typer.models.OptionInfo)
        else None
    )

    # --temp-dir cannot be used alone without --ssd-staging
    if temp_dir_val is not None and not ssd_staging:
        if json_output:
            import json

            print(
                json.dumps(
                    {
                        "error": "--temp-dir cannot be used without enabling --ssd-staging.",
                    }
                )
            )
            raise typer.Exit(1)
        console.print(
            Panel(
                "[bold red]❌ Invalid option combination:[/bold red] "
                "[yellow]--temp-dir[/yellow] cannot be used without enabling [bold cyan]--ssd-staging[/bold cyan].\n\n"
                "To use a custom staging folder, specify both flags:\n"
                f"  [bold cyan]slim-video --ssd-staging --temp-dir '{temp_dir_val}'[/bold cyan]",
                title="⚠️ Option Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    active_temp_dir = temp_dir_val if temp_dir_val is not None else cfg.temp_dir
    active_staging_path: Optional[Path] = Path(active_temp_dir) if active_ssd_staging else None

    try:
        run_main_workflow(
            path_arg=path,
            min_gain=active_min_gain,
            quality=active_quality,
            sample_seconds=active_sample_sec,
            run_samples=run_samples,
            yes=yes,
            dry_run=dry_run,
            all_codecs=active_all_codecs,
            delete_original=active_delete_original,
            staging_dir=active_staging_path,
            history_manager=history,
            interactive_folder_prompt=lambda: prompt_interactive_folder_selection(
                on_estimate=lambda target: cmd_estimate(path=target),
                on_doctor=lambda: cmd_doctor(benchmark=True),
                on_config=lambda: cmd_config_wizard(),
                on_history=lambda: cmd_history_stats(),
            ),
            find_candidates_fn=find_h264_candidates,
            json_output=json_output,
        )
    except KeyboardInterrupt:
        if not json_output:
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
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON format for scripting and automation.",
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
        delete_original=False,
        ssd_staging=False,
        temp_dir=None,
        json_output=json_output,
    )


# ---------------------------------------------------------------------------
# Backwards Compatibility Aliases
# ---------------------------------------------------------------------------

_prompt_interactive_folder_selection = prompt_interactive_folder_selection
_run_main_workflow = run_main_workflow
_execute_batch = execute_batch
_display_estimation_table = display_estimation_table


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
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output diagnostic results as JSON format.",
    ),
) -> None:
    """Run full system diagnostic and hardware verification."""
    with console.status("[bold cyan]Running diagnostic checks…[/bold cyan]"):
        results = run_all_doctor_checks(include_benchmark=benchmark)

    if json_output:
        import json

        data = [
            {"name": r.name, "passed": r.passed, "critical": r.critical, "details": r.details}
            for r in results
        ]
        print(json.dumps(data, indent=2, ensure_ascii=False))
        if not all(r.passed for r in results if r.critical):
            raise typer.Exit(1)
        return

    console.print(
        Panel.fit(
            "[bold cyan]slim-video Doctor[/bold cyan] ── [bold white]System & Hardware Diagnostics[/bold white]\n"
            "[dim]Verifies ffmpeg, ffprobe, VideoToolbox hardware acceleration, and environment health[/dim]",
            border_style="cyan",
        )
    )

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
def cmd_config_show(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output configuration settings as JSON format.",
    ),
) -> None:
    """Display current configuration in a table or JSON."""
    cfg = config_manager.load()
    if json_output:
        import json

        print(json.dumps(cfg.model_dump(), indent=2, ensure_ascii=False))
        return

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
        "delete_original": "Whether to permanently delete original files after transcoding instead of moving to quarantine",
        "all_codecs": "Whether to process all non-HEVC video formats or only H.264",
        "encoder": "FFmpeg HEVC video encoder (default: hevc_videotoolbox)",
        "ssd_staging": "Whether to use SSD staging directory during transcoding (avoids HDD head-thrashing)",
        "temp_dir": "Temporary SSD directory used when ssd_staging is enabled",
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
    try:
        run_config_wizard(config_manager)
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
def cmd_history_stats(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output history statistics as JSON format.",
    ),
) -> None:
    """Show overall stats and recent entries."""
    if not history.path.exists():
        if json_output:
            import json

            print(
                json.dumps(
                    {"stats": {"total_transcodes": 0, "saved_bytes": 0}, "recent_transcodes": []}
                )
            )
            return
        console.print("[dim]No history recorded yet.[/dim]\n")
        return

    stats = history.get_stats()
    all_data = history.get_all()
    transcodes = all_data.get("transcodes", [])

    if json_output:
        import json

        out = {
            "stats": stats,
            "recent_transcodes": transcodes[-10:],
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

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
