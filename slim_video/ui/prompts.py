"""Interactive terminal menus and wizards powered by InquirerPy and Rich."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable, Optional

from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel

from slim_video import __version__
from slim_video.config import ConfigManager

console = Console()


def prompt_interactive_folder_selection(
    on_estimate: Optional[Callable[[str], None]] = None,
    on_doctor: Optional[Callable[[], None]] = None,
    on_config: Optional[Callable[[], None]] = None,
    on_history: Optional[Callable[[], None]] = None,
) -> str:
    """Display an interactive menu to choose folder or utility.

    Args:
        on_estimate: Optional callback when 'Estimate' is chosen.
        on_doctor: Optional callback when 'Doctor' is chosen.
        on_config: Optional callback when 'Configuration' is chosen.
        on_history: Optional callback when 'History' is chosen.

    Returns:
        Selected folder path string.
    """
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
    elif choice.startswith("📊 Estimate") and on_estimate:
        target = inquirer.text(message="Folder to estimate:", default=cwd_path).execute()
        on_estimate(str(target))
        sys.exit(0)
    elif choice.startswith("🩺 Run Hardware") and on_doctor:
        on_doctor()
        sys.exit(0)
    elif choice.startswith("⚙️  Open Configuration") and on_config:
        on_config()
        sys.exit(0)
    elif choice.startswith("📈 View Lifetime") and on_history:
        on_history()
        sys.exit(0)
    else:
        console.print("[dim]Goodbye![/dim]")
        sys.exit(0)


def run_config_wizard(config_manager: ConfigManager) -> None:
    """Guide user through updating all settings interactively.

    Args:
        config_manager: ConfigManager instance to read from and write to.
    """
    cfg = config_manager.load()
    console.print(
        Panel(
            "[bold cyan]🧙 slim-video Configuration Wizard[/bold cyan]\n"
            "[dim]Press Enter to accept current value or type a new one:[/dim]",
            border_style="cyan",
        )
    )

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

    new_ssd_staging = inquirer.confirm(
        message="Use SSD staging directory (/tmp/slim-video) to eliminate head-thrashing on external HDDs?",
        default=cfg.ssd_staging,
    ).execute()

    new_temp_dir = inquirer.text(
        message="Custom temporary directory for SSD staging:",
        default=cfg.temp_dir,
    ).execute()

    config_manager.set("min_gain_percent", new_gain)
    config_manager.set("sample_duration_seconds", new_duration)
    config_manager.set("quality", new_quality)
    config_manager.set("auto_sample_test", str(new_auto_sample))
    config_manager.set("quarantine_dir", new_quarantine)
    config_manager.set("delete_original", str(new_delete_original))
    config_manager.set("ssd_staging", str(new_ssd_staging))
    config_manager.set("temp_dir", new_temp_dir)

    console.print("\n[bold green]✅ All settings updated successfully![/bold green]\n")
