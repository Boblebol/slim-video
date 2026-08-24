# Contributing to hevc-cli

Thank you for your interest in improving **hevc-cli**! We welcome contributions, bug reports, and feature requests.

---

## 🛠 Development Setup

### 1. Prerequisites

- macOS with Apple Silicon (recommended for hardware encoding testing)
- Python ≥ 3.9
- FFmpeg with VideoToolbox support (`brew install ffmpeg`)

### 2. Clone and Install in Editable Mode

```bash
git clone https://github.com/Boblebol/slim-video.git
cd slim-video
pip install -e ".[dev]"
```

### 3. Verify System Health

Run the built-in diagnostic tool to ensure your development environment is ready:

```bash
hevc-cli doctor
```

---

## 🧪 Running Tests & Linting

### Unit Tests

Run the complete test suite with `pytest`:

```bash
pytest tests/ -v
```

To run the live hardware diagnostic benchmark test:

```bash
pytest tests/test_system_doctor.py -v
```

### Code Formatting & Linting

We use [Ruff](https://github.com/astral-sh/ruff) for code formatting and linting:

```bash
# Check code style and lints
ruff check hevc_cli/ tests/

# Automatically format code
ruff format hevc_cli/ tests/
```

---

## 📐 Project Architecture

```
hevc_cli/
├── __init__.py         # Package metadata and versioning
├── __main__.py         # python -m hevc_cli entrypoint
├── models.py           # Core data classes (FileItem, TreeNode, TranscodeRecord, etc.)
├── doctor.py           # System diagnostics & hardware benchmark
├── config.py           # Persistent configuration management (~/.hevc_cli_config.json)
├── probing.py          # Media metadata extraction & file discovery (ffprobe)
├── estimator.py        # 20s middle sample estimation engine
├── transcoder.py       # Hardware-accelerated HEVC transcoding engine
├── tree_selector.py    # Interactive TUI collapsible tree selector (curses)
├── report.py           # Formatted summary text report generator
├── history.py          # Persistent session history store
├── core.py             # Public API facade
└── cli.py              # Typer CLI application
```

---

## 📝 Pull Request Guidelines

1. **Create a branch**: `git checkout -b feature/my-new-feature`
2. **Follow style**: Ensure all type annotations are present and docstrings are provided.
3. **Add tests**: Add unit tests in `tests/` covering your changes.
4. **Run tests and linter**: Make sure `pytest` and `ruff check` pass with 0 warnings.
5. **Submit PR**: Open a pull request with a clear description of your changes.
