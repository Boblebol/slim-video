# Contributing to slim-video

Thank you for your interest in improving **slim-video**! We welcome contributions, bug reports, and feature requests.

---

## 🛠 Development Setup

### 1. Prerequisites

- macOS with Apple Silicon (recommended for VideoToolbox hardware encoding testing)
- Python ≥ 3.9 (or [uv](https://github.com/astral-sh/uv))
- FFmpeg with VideoToolbox support (`brew install ffmpeg`)

### 2. Clone and Install in Editable Mode

```bash
git clone https://github.com/Boblebol/slim-video.git
cd slim-video
uv sync --all-extras --dev
# or with pip: pip install -e ".[dev]"
```

### 3. Verify System Health

Run the built-in diagnostic tool to ensure your development environment is ready:

```bash
slim-video doctor
```

---

## 🧪 Running Tests & Quality Checks

### Unit Tests

Run the complete test suite with `pytest`:

```bash
uv run pytest tests/ -v
```

To run the live hardware diagnostic benchmark test:

```bash
uv run pytest tests/test_system_doctor.py -v
```

### Code Formatting, Linting & Type Checking

```bash
# Lint check with Ruff
uv run ruff check slim_video/ tests/

# Code formatting check
uv run ruff format --check slim_video/ tests/

# Strict static type analysis with Mypy
uv run mypy slim_video/
```

---

## 📐 Project Architecture

```
slim_video/
├── __init__.py         # Package metadata and public exports
├── __main__.py         # python -m slim_video entrypoint
├── models.py           # Pydantic v2 data models (FileItem, TreeNode, TranscodeRecord, etc.)
├── doctor.py           # System diagnostics & VideoToolbox hardware benchmark
├── config.py           # Persistent configuration management (~/.slim_video_config.json)
├── probing.py          # Media metadata extraction & file discovery (ffprobe)
├── estimator.py        # 20s middle sample estimation engine
├── transcoder.py       # Hardware-accelerated HEVC transcoding engine with quarantine safety
├── tree_selector.py    # Interactive TUI collapsible tree selector (curses)
├── report.py           # Formatted summary text report generator
├── history.py          # Persistent session history store (~/.slim_video_history.json)
├── core.py             # Public API facade
└── cli.py              # Typer CLI application
```

---

## 📜 Conventional Commits & Pull Request Guidelines

This project strictly follows the **[Conventional Commits 1.0.0](https://www.conventionalcommits.org/)** specification.

### Allowed Commit Types

- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation only changes
- `style:` Code formatting, white-space, missing semi-colons
- `refactor:` Code refactoring without fixing a bug or adding a feature
- `perf:` Performance improvements
- `test:` Adding or updating tests
- `build:` Build system or dependencies (`uv`, `pyproject.toml`)
- `ci:` Continuous Integration changes (`.github/workflows/`)
- `chore:` Other changes that don't modify src or test files

### Example Commits

```bash
feat(transcoder): add 10-bit color profile support
fix(tree): prevent terminal overflow on small screens
docs(readme): add cli usage examples and badges
test(doctor): add automated hardware validation test
```

### Pull Request Workflow

1. **Create a branch**: `git checkout -b feat/my-new-feature`
2. **Commit with Conventional Commits**: `git commit -m "feat(module): description"`
3. **Verify checks locally**: `uv run ruff check slim_video/ tests/ && uv run mypy slim_video/ && uv run pytest tests/ -v`
4. **Open a PR**: Title must follow Conventional Commits (e.g. `feat(module): my contribution`).
