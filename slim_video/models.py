"""Pydantic v2 models and data transfer objects (DTOs) for slim-video."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class FileItem(BaseModel):
    """Represents a discovered video file candidate."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    rel_path: Path
    size: int
    codec: str = "h264"
    resolution: str = "Unknown"
    fps: float = 0.0
    duration: float = 0.0
    audio: str = ""
    selected: bool = True
    estimated_size: Optional[int] = None
    estimated_gain_pct: Optional[float] = None
    below_threshold: bool = False

    def __init__(
        self,
        path: Path,
        rel_path: Path,
        size: int,
        codec: str = "h264",
        resolution: str = "Unknown",
        fps: float = 0.0,
        duration: float = 0.0,
        audio: str = "",
        selected: bool = True,
        estimated_size: Optional[int] = None,
        estimated_gain_pct: Optional[float] = None,
        below_threshold: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            path=path,
            rel_path=rel_path,
            size=size,
            codec=codec,
            resolution=resolution,
            fps=fps,
            duration=duration,
            audio=audio,
            selected=selected,
            estimated_size=estimated_size,
            estimated_gain_pct=estimated_gain_pct,
            below_threshold=below_threshold,
            **kwargs,
        )


class TreeNode:
    """Hierarchical node in the directory/file tree structure."""

    def __init__(
        self,
        name: str,
        is_dir: bool,
        path: Path,
        rel_path: Path,
        file_item: Optional[FileItem] = None,
        parent: Optional[TreeNode] = None,
    ) -> None:
        self.name: str = name
        self.is_dir: bool = is_dir
        self.path: Path = path
        self.rel_path: Path = rel_path
        self.file_item: Optional[FileItem] = file_item
        self.parent: Optional[TreeNode] = parent
        self.children: list[TreeNode] = []
        self.expanded: bool = True

    def get_all_file_items(self) -> list[FileItem]:
        """Return all descendant FileItem instances recursively."""
        if not self.is_dir and self.file_item:
            return [self.file_item]
        items: list[FileItem] = []
        for child in self.children:
            items.extend(child.get_all_file_items())
        return items

    @property
    def total_size(self) -> int:
        """Total size in bytes of all descendant files."""
        return sum(f.size for f in self.get_all_file_items())

    @property
    def selected_size(self) -> int:
        """Total size in bytes of selected descendant files."""
        return sum(f.size for f in self.get_all_file_items() if f.selected)

    @property
    def selected_estimated_size(self) -> int:
        """Total estimated size in bytes of selected descendant files."""
        return sum(
            (f.estimated_size if f.estimated_size is not None else f.size)
            for f in self.get_all_file_items()
            if f.selected
        )

    @property
    def total_files(self) -> int:
        """Total count of descendant files."""
        return len(self.get_all_file_items())

    @property
    def selected_files(self) -> int:
        """Total count of selected descendant files."""
        return sum(1 for f in self.get_all_file_items() if f.selected)

    def is_all_selected(self) -> bool:
        """True if all descendant files are selected."""
        files = self.get_all_file_items()
        return bool(files) and all(f.selected for f in files)

    def is_none_selected(self) -> bool:
        """True if no descendant files are selected."""
        files = self.get_all_file_items()
        return not files or all(not f.selected for f in files)

    def is_partially_selected(self) -> bool:
        """True if some (but not all) descendant files are selected."""
        files = self.get_all_file_items()
        if not files:
            return False
        sel = sum(1 for f in files if f.selected)
        return 0 < sel < len(files)

    def toggle_selection(self) -> None:
        """Toggle selection for file or directory."""
        if self.is_dir:
            if self.is_all_selected():
                for f in self.get_all_file_items():
                    f.selected = False
            else:
                for f in self.get_all_file_items():
                    f.selected = True
        elif self.file_item:
            self.file_item.selected = not self.file_item.selected

    def toggle_expanded(self) -> None:
        """Toggle folder expansion."""
        if self.is_dir:
            self.expanded = not self.expanded

    def expand_all(self, recursive: bool = True) -> None:
        """Expand folder and optionally all child folders."""
        if self.is_dir:
            self.expanded = True
            if recursive:
                for child in self.children:
                    child.expand_all(recursive=True)

    def collapse_all(self, recursive: bool = True) -> None:
        """Collapse folder and optionally all child folders."""
        if self.is_dir:
            self.expanded = False
            if recursive:
                for child in self.children:
                    child.collapse_all(recursive=True)


class TranscodeRecord(BaseModel):
    """Detailed record for a single processed video file."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: str
    rel_path: str
    codec: str
    resolution: str
    fps: float
    duration: float
    audio: str
    original_size: int
    final_size: int
    gain_pct: float
    saved_bytes: int
    elapsed_seconds: float
    speed: str
    output_path: Optional[str] = None
    quarantine_path: Optional[str] = None
    status: str = "ok"  # "ok", "error", "skipped"
    error_message: Optional[str] = None


class BatchSummary(BaseModel):
    """Summary of a full transcoding session."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    directory: Path
    encoder_name: str = "Apple VideoToolbox (hevc_videotoolbox - 10-bit)"
    start_time: str = ""
    end_time: str = ""
    total_duration_sec: float = 0.0
    total_files_scanned: int = 0
    total_files_selected: int = 0
    total_files_successful: int = 0
    total_files_failed: int = 0
    total_original_bytes: int = 0
    total_final_bytes: int = 0
    total_saved_bytes: int = 0
    total_gain_pct: float = 0.0
    records: list[TranscodeRecord] = Field(default_factory=list)


class DoctorCheckResult(BaseModel):
    """Result of a diagnostic environment check."""

    name: str
    passed: bool
    details: str
    critical: bool = True
