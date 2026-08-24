"""Live validation test to guarantee slim-video is properly installed and runnable on this PC."""

from __future__ import annotations

from typer.testing import CliRunner

from slim_video.cli import app
from slim_video.doctor import run_all_doctor_checks

runner = CliRunner()


def test_system_doctor_checks_pass_on_this_machine() -> None:
    """Validate that environment dependencies are present on this machine."""
    checks = run_all_doctor_checks(include_benchmark=True)
    failing_critical = [c for c in checks if not c.passed and c.critical]

    if failing_critical:
        errors = "\n".join(f"- {c.name}: {c.details}" for c in failing_critical)
        raise AssertionError(f"Critical system checks failed on this PC:\n{errors}")


def test_doctor_cli_command_live_execution() -> None:
    """Validate that `slim-video doctor` runs with exit code 0."""
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, f"Doctor CLI failed:\n{result.output}"
    assert "All checks passed" in result.output or "Ready to Transcode" in result.output
