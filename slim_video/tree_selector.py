"""Interactive terminal tree view selector for video files.

Provides a collapsible, checkbox-enabled file tree navigation (fold/unfold directories,
check/uncheck files and directories) powered by curses with real sample estimation displays.
"""

from __future__ import annotations

import curses
import locale
import sys
from pathlib import Path

from slim_video.formatting import fit_terminal_text, fmt_bytes, fmt_duration
from slim_video.models import FileItem, TreeNode

__all__ = [
    "build_file_tree",
    "fit_terminal_text",
    "fmt_bytes",
    "fmt_duration",
    "get_visible_rows",
    "select_files_interactive",
]


def build_file_tree(root: Path, file_items: list[FileItem]) -> TreeNode:
    """Build a hierarchical tree structure from a list of FileItem objects."""
    root_node = TreeNode(
        name=root.name or str(root),
        is_dir=True,
        path=root,
        rel_path=Path("."),
    )

    dir_nodes: dict[Path, TreeNode] = {Path("."): root_node}

    for item in file_items:
        parent_rel = item.rel_path.parent
        current_rel = Path(".")
        current_node = root_node

        for part in parent_rel.parts:
            if part in (".", ""):
                continue
            current_rel = current_rel / part
            if current_rel not in dir_nodes:
                new_dir = TreeNode(
                    name=part,
                    is_dir=True,
                    path=root / current_rel,
                    rel_path=current_rel,
                    parent=current_node,
                )
                current_node.children.append(new_dir)
                dir_nodes[current_rel] = new_dir
            current_node = dir_nodes[current_rel]

        file_node = TreeNode(
            name=item.path.name,
            is_dir=False,
            path=item.path,
            rel_path=item.rel_path,
            file_item=item,
            parent=current_node,
        )
        current_node.children.append(file_node)

    def _sort_node(node: TreeNode) -> None:
        node.children.sort(key=lambda n: (not n.is_dir, n.name.lower()))
        for child in node.children:
            if child.is_dir:
                _sort_node(child)

    _sort_node(root_node)
    return root_node


def get_visible_rows(node: TreeNode, depth: int = 0) -> list[tuple[TreeNode, int]]:
    """Return flattened list of (TreeNode, depth) for all currently visible/expanded nodes."""
    rows: list[tuple[TreeNode, int]] = []
    if node.parent is None:
        # Virtual root node - iterate through its top-level children
        for child in node.children:
            rows.extend(get_visible_rows(child, 0))
        return rows

    rows.append((node, depth))
    if node.is_dir and node.expanded:
        for child in node.children:
            rows.extend(get_visible_rows(child, depth + 1))
    return rows


def _safe_addstr(stdscr: curses.window, y: int, x: int, text: str, attr: int = 0) -> None:
    """Safely write string to curses window without overflowing boundaries."""
    max_y, max_x = stdscr.getmaxyx()
    if y < 0 or y >= max_y or x < 0 or x >= max_x:
        return
    available = max_x - x
    if available <= 0:
        return
    if y == max_y - 1 and len(text) >= available:
        text = text[: available - 1]
    else:
        text = text[:available]
    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def _interactive_tree_loop(
    stdscr: curses.window,
    root: Path,
    file_items: list[FileItem],
) -> list[FileItem]:
    """Curses main loop for interactive tree selection."""
    try:
        locale.setlocale(locale.LC_ALL, "")
    except Exception:
        pass

    curses.curs_set(0)
    curses.use_default_colors()

    # Color definitions
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(6, curses.COLOR_YELLOW, -1)
    curses.init_pair(7, curses.COLOR_RED, -1)

    tree = build_file_tree(root, file_items)
    cursor_idx = 0
    scroll_offset = 0

    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        visible_rows = get_visible_rows(tree)
        if not visible_rows:
            visible_rows = [(tree, 0)]

        if cursor_idx >= len(visible_rows):
            cursor_idx = max(0, len(visible_rows) - 1)

        # Header - full width
        header_text = " 🎬  slim-video — Video Selection for HEVC / x265 Transcoding "
        _safe_addstr(stdscr, 0, 0, header_text.ljust(max_x), curses.color_pair(4) | curses.A_BOLD)

        total_files = tree.total_files
        total_size = tree.total_size
        dir_info = (
            f" 📁  Directory: {root}  ({total_files} candidate file(s), {fmt_bytes(total_size)})"
        )
        _safe_addstr(stdscr, 1, 0, dir_info.ljust(max_x), curses.A_BOLD)
        _safe_addstr(stdscr, 2, 0, "─" * (max_x - 1), curses.color_pair(2))

        # Viewport dimensions
        header_height = 3
        footer_height = 2
        viewport_height = max(1, max_y - header_height - footer_height)

        # Adjust scroll offset
        if cursor_idx < scroll_offset:
            scroll_offset = cursor_idx
        elif cursor_idx >= scroll_offset + viewport_height:
            scroll_offset = cursor_idx - viewport_height + 1

        # Render visible rows
        for line_idx in range(viewport_height):
            item_idx = scroll_offset + line_idx
            if item_idx >= len(visible_rows):
                break

            node, depth = visible_rows[item_idx]
            y = header_height + line_idx
            is_cursor = item_idx == cursor_idx

            indent = "  " * depth

            if node.is_dir:
                # Checkbox
                if node.is_all_selected():
                    chk = "[x] "
                    chk_color = curses.color_pair(3) | curses.A_BOLD
                elif node.is_partially_selected():
                    chk = "[-] "
                    chk_color = curses.color_pair(6) | curses.A_BOLD
                else:
                    chk = "[ ] "
                    chk_color = curses.color_pair(1) | curses.A_DIM

                expander = "▼ " if node.expanded else "▶ "
                meta_str = f"({node.total_files} file{'s' if node.total_files > 1 else ''} · {fmt_bytes(node.total_size)})"
                left_prefix = f"{indent}{chk}{expander}📁 "

                # Responsive width calculation
                avail_name = max(5, max_x - len(left_prefix) - len(meta_str) - 3)
                dir_display = node.name + "/"
                if len(dir_display) > avail_name:
                    dir_display = fit_terminal_text(dir_display, avail_name)

                meta_x = max(len(left_prefix) + len(dir_display) + 2, max_x - len(meta_str) - 2)

                if is_cursor:
                    full_line = f"{left_prefix}{dir_display}".ljust(meta_x) + meta_str
                    _safe_addstr(
                        stdscr,
                        y,
                        0,
                        full_line.ljust(max_x - 1),
                        curses.A_REVERSE | curses.A_BOLD,
                    )
                else:
                    _safe_addstr(stdscr, y, 0, indent, curses.color_pair(1))
                    pos = len(indent)
                    _safe_addstr(stdscr, y, pos, chk, chk_color)
                    pos += len(chk)
                    _safe_addstr(
                        stdscr,
                        y,
                        pos,
                        f"{expander}📁 {dir_display}",
                        curses.color_pair(2) | curses.A_BOLD,
                    )
                    _safe_addstr(stdscr, y, meta_x, meta_str, curses.color_pair(1) | curses.A_DIM)

            else:
                item = node.file_item
                if item and item.selected:
                    chk = "[x] "
                    chk_color = curses.color_pair(3) | curses.A_BOLD
                else:
                    chk = "[ ] "
                    chk_color = curses.color_pair(1) | curses.A_DIM

                # Construct right-side metadata badge
                codec_name = item.codec.upper() if item else "H264"
                res_str = item.resolution if item else ""
                audio_str = (
                    f" · {item.audio}" if (item and item.audio and item.audio != "No audio") else ""
                )
                spec_str = f"[{codec_name} {res_str}{audio_str}]" if res_str else f"[{codec_name}]"
                orig_size_str = fmt_bytes(item.size if item else 0)

                est_tag = ""
                est_color = curses.color_pair(1)
                if item and item.estimated_gain_pct is not None:
                    if item.below_threshold:
                        est_tag = f" → ~{fmt_bytes(item.estimated_size or 0)} ({item.estimated_gain_pct:+.1f}% < min ⏭)"
                        est_color = curses.color_pair(6)
                    else:
                        est_tag = f" → ~{fmt_bytes(item.estimated_size or 0)} (-{item.estimated_gain_pct:.1f}% ✅)"
                        est_color = curses.color_pair(3)

                # Right metadata
                right_full = f"{spec_str}  {orig_size_str}{est_tag}"
                left_prefix = f"{indent}{chk}🎬 "

                # Responsive adjustments for smaller screens
                avail_name = max_x - len(left_prefix) - len(right_full) - 3
                if avail_name < 15 and audio_str:
                    spec_str = f"[{codec_name} {res_str}]"
                    right_full = f"{spec_str}  {orig_size_str}{est_tag}"
                    avail_name = max_x - len(left_prefix) - len(right_full) - 3
                if avail_name < 10:
                    right_full = f"{orig_size_str}{est_tag}"
                    avail_name = max_x - len(left_prefix) - len(right_full) - 3

                avail_name = max(6, avail_name)
                file_display = node.name
                if len(file_display) > avail_name:
                    file_display = fit_terminal_text(file_display, avail_name)

                right_x = max(
                    len(left_prefix) + len(file_display) + 2,
                    max_x - len(right_full) - 2,
                )

                if is_cursor:
                    full_line = f"{left_prefix}{file_display}".ljust(right_x) + right_full
                    _safe_addstr(
                        stdscr,
                        y,
                        0,
                        full_line.ljust(max_x - 1),
                        curses.A_REVERSE | curses.A_BOLD,
                    )
                else:
                    _safe_addstr(stdscr, y, 0, indent, curses.color_pair(1))
                    pos = len(indent)
                    _safe_addstr(stdscr, y, pos, chk, chk_color)
                    pos += len(chk)
                    _safe_addstr(stdscr, y, pos, f"🎬 {file_display}", curses.color_pair(1))

                    # Render right-hand side specs and gain
                    curr_x = right_x
                    _safe_addstr(stdscr, y, curr_x, spec_str, curses.color_pair(2))
                    curr_x += len(spec_str) + 2
                    _safe_addstr(
                        stdscr, y, curr_x, orig_size_str, curses.color_pair(1) | curses.A_BOLD
                    )
                    curr_x += len(orig_size_str)
                    if est_tag:
                        _safe_addstr(stdscr, y, curr_x, est_tag, est_color)

        # Footer / Help bar
        sel_count = tree.selected_files
        sel_size = tree.selected_size
        sel_est = tree.selected_estimated_size

        if sel_size > 0 and sel_est < sel_size:
            saved_est = sel_size - sel_est
            pct_est = (saved_est / sel_size) * 100
            footer_top = (
                f" Selected: {sel_count}/{total_files} files "
                f"({fmt_bytes(sel_size)} → ~{fmt_bytes(sel_est)}, Est. Gain: -{pct_est:.1f}%)"
            )
        else:
            footer_top = f" Selected: {sel_count}/{total_files} files ({fmt_bytes(sel_size)} / {fmt_bytes(total_size)})"

        _safe_addstr(stdscr, max_y - 2, 0, "─" * (max_x - 1), curses.color_pair(2))
        _safe_addstr(stdscr, max_y - 2, 2, f" {footer_top} ", curses.color_pair(3) | curses.A_BOLD)

        help_bar = " [↑/↓/j/k] Move  [Space] Select  [←/→/h/l] Fold/Unfold  [a] All  [e/c] Expand/Collapse  [Enter] Start  [q] Quit "
        _safe_addstr(
            stdscr, max_y - 1, 0, help_bar.ljust(max_x - 1), curses.color_pair(5) | curses.A_BOLD
        )

        stdscr.refresh()

        # Keyboard input
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            return []

        if key in (ord("q"), ord("Q"), 27):  # 'q' or ESC
            return []

        elif key in (curses.KEY_UP, ord("k"), ord("K")):
            cursor_idx = max(0, cursor_idx - 1)

        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            cursor_idx = min(len(visible_rows) - 1, cursor_idx + 1)

        elif key in (curses.KEY_PPAGE, 2, 21):  # Page Up, Ctrl+B, Ctrl+U
            cursor_idx = max(0, cursor_idx - viewport_height)

        elif key in (curses.KEY_NPAGE, 6, 4):  # Page Down, Ctrl+F, Ctrl+D
            cursor_idx = min(len(visible_rows) - 1, cursor_idx + viewport_height)

        elif key in (curses.KEY_HOME, ord("g")):
            cursor_idx = 0

        elif key in (curses.KEY_END, ord("G")):
            cursor_idx = len(visible_rows) - 1

        elif key == ord(" "):  # Space to toggle selection
            if 0 <= cursor_idx < len(visible_rows):
                node, _ = visible_rows[cursor_idx]
                node.toggle_selection()

        elif key in (curses.KEY_RIGHT, ord("l"), ord("L")):  # Expand or go into
            if 0 <= cursor_idx < len(visible_rows):
                node, _ = visible_rows[cursor_idx]
                if node.is_dir:
                    if not node.expanded:
                        node.expanded = True
                    elif node.children:
                        cursor_idx = min(len(visible_rows) - 1, cursor_idx + 1)

        elif key in (curses.KEY_LEFT, ord("h"), ord("H")):  # Collapse or go to parent
            if 0 <= cursor_idx < len(visible_rows):
                node, _ = visible_rows[cursor_idx]
                if node.is_dir and node.expanded:
                    node.expanded = False
                elif node.parent is not None:
                    # Move cursor to parent
                    for i, (vnode, _) in enumerate(visible_rows):
                        if vnode == node.parent:
                            cursor_idx = i
                            break

        elif key in (ord("o"), ord("O")):  # Toggle expand folder
            if 0 <= cursor_idx < len(visible_rows):
                node, _ = visible_rows[cursor_idx]
                if node.is_dir:
                    node.toggle_expanded()

        elif key in (ord("e"), ord("E"), ord("+")):  # Expand all
            tree.expand_all()

        elif key in (ord("c"), ord("C"), ord("-")):  # Collapse all
            tree.collapse_all()

        elif key in (ord("a"), ord("A")):  # Toggle all selection
            tree.toggle_selection()

        elif key in (curses.KEY_ENTER, 10, 13):  # Enter to confirm
            return [item for item in file_items if item.selected]

        elif key == curses.KEY_RESIZE:
            continue

    return [item for item in file_items if item.selected]


def select_files_interactive(
    root: Path,
    file_items: list[FileItem],
    non_interactive: bool = False,
) -> list[FileItem]:
    """Display interactive file tree selector or fallback to non-interactive mode."""
    if not file_items:
        return []

    if non_interactive or not sys.stdin.isatty():
        return [f for f in file_items if f.selected]

    try:
        return curses.wrapper(_interactive_tree_loop, root, file_items)
    except Exception as exc:
        print(f"[tree_selector] Curses fallback ({exc}) - selecting all candidate files.")
        return [f for f in file_items if f.selected]
