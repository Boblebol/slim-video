"""Persistent history tracking for test sessions and transcoding jobs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from slim_video.constants import DEFAULT_HISTORY_FILE

_EMPTY_STORE: dict[str, list[dict[str, Any]]] = {"tests": [], "transcodes": []}


MAX_HISTORY_TESTS: int = 500
MAX_HISTORY_TRANSCODES: int = 2000


class HistoryManager:
    """JSON-backed store that records estimation tests and transcode jobs.

    The history file lives at ``~/.slim_video_history.json`` by default and
    persists across CLI sessions. All writes are atomic via a full file
    re-write (the store is small enough that this is fine).

    Args:
        path: Override the default history file location.
    """

    def __init__(self, path: Path = DEFAULT_HISTORY_FILE) -> None:
        self.path: Path = path
        if not self.path.exists():
            self._write(_EMPTY_STORE.copy())

    # ------------------------------------------------------------------
    # Internal I/O
    # ------------------------------------------------------------------

    def _read(self) -> dict[str, list[dict[str, Any]]]:
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure both keys exist even in older history files
                data.setdefault("tests", [])
                data.setdefault("transcodes", [])
                result: dict[str, list[dict[str, Any]]] = data
                return result
        except Exception:
            return _EMPTY_STORE.copy()

    def _write(self, data: dict[str, Any]) -> None:
        try:
            with self.path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            # Non-fatal: history is a convenience feature, not mission-critical
            print(f"[history] Warning: could not write history — {exc}")

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------------
    # Write API
    # ------------------------------------------------------------------

    def record_test(
        self,
        *,
        file_path: str,
        codec: str,
        original_size: int,
        estimated_size: int,
        gain_pct: float,
        ratio: float,
        quality: int,
    ) -> None:
        """Record a sample-based estimation result."""
        data = self._read()
        data["tests"].append(
            {
                "timestamp": self._now(),
                "file": file_path,
                "name": Path(file_path).name,
                "codec": codec,
                "original_size": original_size,
                "estimated_size": estimated_size,
                "gain_pct": gain_pct,
                "ratio": ratio,
                "quality": quality,
            }
        )
        if len(data["tests"]) > MAX_HISTORY_TESTS:
            data["tests"] = data["tests"][-MAX_HISTORY_TESTS:]
        self._write(data)

    def record_transcode(
        self,
        *,
        file_path: str,
        codec: str,
        original_size: int,
        final_size: int,
        gain_pct: float,
        quality: int,
        status: str,
    ) -> None:
        """Record a completed (or failed) transcode job."""
        data = self._read()
        data["transcodes"].append(
            {
                "timestamp": self._now(),
                "file": file_path,
                "name": Path(file_path).name,
                "codec": codec,
                "original_size": original_size,
                "final_size": final_size,
                "gain_pct": gain_pct,
                "quality": quality,
                "status": status,
            }
        )
        if len(data["transcodes"]) > MAX_HISTORY_TRANSCODES:
            data["transcodes"] = data["transcodes"][-MAX_HISTORY_TRANSCODES:]
        self._write(data)

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------

    def get_all(self) -> dict[str, list[dict[str, Any]]]:
        """Return the full history store."""
        return self._read()

    def get_stats(self) -> dict[str, Any]:
        """Return aggregated statistics across all recorded transcodes.

        Returns:
            Dictionary with:
                - ``total_tests``: Number of estimation tests run.
                - ``total_transcodes``: Total transcode attempts.
                - ``successful_transcodes``: Transcodes with status ``"ok"``.
                - ``original_bytes``: Sum of source sizes for successful jobs.
                - ``final_bytes``: Sum of output sizes for successful jobs.
                - ``saved_bytes``: ``original_bytes - final_bytes``.
                - ``overall_gain_pct``: Cumulative storage reduction in percent.
        """
        data = self._read()
        ok = [t for t in data["transcodes"] if t.get("status") == "ok"]
        original = sum(t.get("original_size", 0) for t in ok)
        final = sum(t.get("final_size", 0) for t in ok)
        saved = max(original - final, 0)
        gain = round(saved / original * 100, 1) if original else 0.0
        return {
            "total_tests": len(data["tests"]),
            "total_transcodes": len(data["transcodes"]),
            "successful_transcodes": len(ok),
            "original_bytes": original,
            "final_bytes": final,
            "saved_bytes": saved,
            "overall_gain_pct": gain,
        }

    def clear(self) -> None:
        """Wipe all recorded history."""
        self._write(_EMPTY_STORE.copy())
