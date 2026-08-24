"""Unit tests for slim_video.tree_selector module."""

from __future__ import annotations

from pathlib import Path

from slim_video.tree_selector import (
    FileItem,
    build_file_tree,
    fmt_bytes,
    fmt_duration,
    get_visible_rows,
    select_files_interactive,
)


def test_fmt_bytes() -> None:
    assert fmt_bytes(500) == "0.5 KB"
    assert fmt_bytes(1_500_000) == "1.4 MB"
    assert fmt_bytes(2_500_000_000) == "2.33 GB"


def test_fmt_duration() -> None:
    assert fmt_duration(0) == "N/A"
    assert fmt_duration(45) == "0m 45s"
    assert fmt_duration(3665) == "1h 01m 05s"


def test_tree_construction_and_hierarchy() -> None:
    root = Path("/media/videos")
    f1 = FileItem(root / "film1.mp4", Path("film1.mp4"), 1_000_000, "h264", "1080p")
    f2 = FileItem(
        root / "Series" / "S01" / "ep01.mkv",
        Path("Series/S01/ep01.mkv"),
        2_000_000,
        "h264",
        "1080p",
    )
    f3 = FileItem(
        root / "Series" / "S01" / "ep02.mkv",
        Path("Series/S01/ep02.mkv"),
        3_000_000,
        "h264",
        "1080p",
    )
    f4 = FileItem(
        root / "Series" / "S02" / "ep01.mkv",
        Path("Series/S02/ep01.mkv"),
        4_000_000,
        "h264",
        "1080p",
    )

    tree = build_file_tree(root, [f1, f2, f3, f4])

    assert tree.is_dir is True
    assert tree.total_files == 4
    assert tree.total_size == 10_000_000
    assert tree.selected_files == 4
    assert tree.selected_size == 10_000_000
    assert tree.is_all_selected() is True
    assert tree.is_partially_selected() is False
    assert tree.is_none_selected() is False


def test_tree_toggle_selection() -> None:
    root = Path("/media/videos")
    f1 = FileItem(root / "f1.mp4", Path("f1.mp4"), 100, selected=True)
    f2 = FileItem(root / "f2.mp4", Path("f2.mp4"), 200, selected=True)
    tree = build_file_tree(root, [f1, f2])

    # Uncheck all
    tree.toggle_selection()
    assert f1.selected is False
    assert f2.selected is False
    assert tree.is_none_selected() is True
    assert tree.selected_files == 0
    assert tree.selected_size == 0

    # Toggle one file
    f1.selected = True
    assert tree.is_partially_selected() is True
    assert tree.is_all_selected() is False
    assert tree.selected_files == 1
    assert tree.selected_size == 100

    # Toggle tree again (since partially selected, it selects all)
    tree.toggle_selection()
    assert f1.selected is True
    assert f2.selected is True
    assert tree.is_all_selected() is True


def test_tree_folder_toggle_selection_nested() -> None:
    root = Path("/media")
    f1 = FileItem(root / "A" / "1.mp4", Path("A/1.mp4"), 100, selected=True)
    f2 = FileItem(root / "A" / "2.mp4", Path("A/2.mp4"), 200, selected=True)
    f3 = FileItem(root / "B" / "3.mp4", Path("B/3.mp4"), 300, selected=True)

    tree = build_file_tree(root, [f1, f2, f3])
    # Find dir A node
    dir_a = next(c for c in tree.children if c.name == "A")
    assert dir_a.is_all_selected() is True

    # Deselect folder A
    dir_a.toggle_selection()
    assert f1.selected is False
    assert f2.selected is False
    assert f3.selected is True
    assert dir_a.is_none_selected() is True
    assert tree.is_partially_selected() is True


def test_tree_folding_unfolding_and_visible_rows() -> None:
    root = Path("/media")
    f1 = FileItem(root / "Series" / "S01" / "1.mp4", Path("Series/S01/1.mp4"), 100)
    tree = build_file_tree(root, [f1])

    # Initially all expanded
    rows = get_visible_rows(tree)
    names = [node.name for node, depth in rows]
    assert names == ["Series", "S01", "1.mp4"]

    # Collapse S01
    dir_s01 = next(n for n, d in rows if n.name == "S01")
    dir_s01.expanded = False
    rows_collapsed = get_visible_rows(tree)
    names_collapsed = [node.name for node, depth in rows_collapsed]
    assert names_collapsed == ["Series", "S01"]

    # Collapse Series
    dir_series = next(n for n, d in rows if n.name == "Series")
    dir_series.expanded = False
    rows_collapsed_series = get_visible_rows(tree)
    names_collapsed_series = [node.name for node, depth in rows_collapsed_series]
    assert names_collapsed_series == ["Series"]

    # Expand all
    tree.expand_all()
    rows_expanded = get_visible_rows(tree)
    assert len(rows_expanded) == 3


def test_select_files_interactive_non_interactive() -> None:
    root = Path("/media")
    f1 = FileItem(root / "a.mp4", Path("a.mp4"), 100, selected=True)
    f2 = FileItem(root / "b.mp4", Path("b.mp4"), 200, selected=False)

    selected = select_files_interactive(root, [f1, f2], non_interactive=True)
    assert selected == [f1]
