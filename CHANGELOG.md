# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.2] - 2026-08-28

### Added
- GitHub branch protection and security gate workflow in `.github/workflows/branch-guard.yml` restricting direct `main` branch pushes strictly to `@Boblebol`.
- Contributor Covenant Code of Conduct v2.1 in `CODE_OF_CONDUCT.md`.
- Explicit repository code ownership assignment to `@Boblebol` in `.github/CODEOWNERS`.
- Structured GitHub Pull Request template with Mermaid architecture diagrams in `.github/PULL_REQUEST_TEMPLATE.md`.
- Standard GitHub Issue templates for bug reports, feature requests, and community links in `.github/ISSUE_TEMPLATE/`.
- Local modular agent skills store provisioned into `.agents/skills/`.

## [1.5.1] - 2026-08-28

### Added
- Complete and comprehensive technical guide and user manual in `DOCUMENTATION.md` detailing internal architecture, Mermaid execution pipeline, full CLI option matrix, SSD staging best practices, Bash scripting integrations, and troubleshooting.
- Revamped marketing-oriented `README.md` featuring value proposition tables, visual feature cards, real-world benchmark metrics, and quickstart guides.
- Direct bidirectional navigation links between `README.md` and `DOCUMENTATION.md`.

## [1.5.0] - 2026-08-28

### Added
- Machine-readable `--json` output across `estimate`, `doctor`, `config show`, and `history stats` for automation, dashboard, and script integrations.
- Automatic non-interactive environment detection (`isatty`) ensuring seamless unattended execution in cron jobs, scripts, and pipes without blocking.
- Native macOS desktop notification upon batch transcoding completion (`display notification` via AppleScript) with summary of freed storage.
- Real-time global batch ETA estimate (`TimeRemainingColumn`) in the Rich progress bar.
- Centralized `slim_video.constants` module consolidating default thresholds, codec sets, and storage paths.
- Centralized `slim_video.formatting` module for byte, duration, label formatting, and desktop notifications.
- Curses help bar hints highlighting Vim keys (`j`/`k` move, `h`/`l` fold/unfold) and quick action keys (`PageUp`/`PageDown`, `Home`/`End`).
- Automated CI test coverage tracking with `pytest-cov` and `coverage.xml` build artifacts.

### Changed
- Major architectural refactoring modularizing `cli.py` (down to 628 lines, -54%), extracting `slim_video.workflow` for batch/dry-run orchestration and `slim_video.ui.prompts` for interactive menus and wizards.
- Decoupled `tree_selector.py` from core transcoding logic and formatting utilities.
- Factorized FFmpeg command generator (`build_transcode_command`) eliminating code duplication between VideoToolbox and libx265 paths.
- Added rolling window caps to `HistoryManager` (`MAX_HISTORY_TESTS = 500`, `MAX_HISTORY_TRANSCODES = 2000`) preventing unbounded file growth.
- Increased automated test coverage to 81% across 95 unit tests.

### Fixed
- Robust subprocess interrupt and termination safety in `estimator.py` terminating and killing child FFmpeg processes on `Ctrl+C` or unexpected exceptions.
- Isolated test environment with autouse fixture preventing modifications to user configuration and history files during test runs.

## [1.4.0] - 2026-08-25

### Added
- SSD Staging mode (`--ssd-staging`) writing intermediate encoded files into fast local SSD storage (`/tmp/slim-video/`) to eliminate head-thrashing and severe I/O bottlenecks on external mechanical HDDs (such as WD Black drives).
- Custom temporary directory option (`--temp-dir <PATH>`) paired with `--ssd-staging` with strict validation to prevent accidental misuse.
- Persistent `ssd_staging` and `temp_dir` configuration settings in `~/.slim_video_config.json` with step-by-step prompts in `slim-video config wizard`.
- Safety pre-flight check guaranteeing at least 2× source file size of free disk space on the staging drive before encoding begins.
- Live file transfer progress indicators and comprehensive structured logging (`logging.getLogger("slim_video.transcoder")`).
- Safe cleanup guarantees ensuring all intermediate `.tmp` files are pruned immediately upon completion or cancellation, and original files are only modified after verified transfer.

## [1.3.0] - 2026-08-25
- Persistent `delete_original` configuration setting in `~/.slim_video_config.json` with step-by-step prompt in `slim-video config wizard`.
- Interactive launcher menu when running `slim-video` in a TTY without arguments (browse current folder, custom path, `~/Movies`, `/Volumes`, config, doctor, history).
- Non-destructive estimation command `slim-video estimate [PATH]` (`--dry-run`) displaying projected savings in a Rich table.
- Animated scan discovery spinner and real-time 2-level sample estimation progress bars displaying active video, resolution, and encoding speed.
- In-depth documentation section in `README.md` detailing lossless audio/subtitle stream copying, 10-bit color mechanics, and H.264 vs H.265 compression efficiency.

### Changed
- Full-width responsive tree viewport (`tree_selector.py`) utilizing total terminal width (`max_x`) with right-aligned metadata and middle-ellipsis (`fit_terminal_text`), eliminating text truncation.
- Dynamic table rendering in Rich with full column expansion (`expand=True`, `overflow="fold"`) across `estimate`, `history stats`, and batch summaries.
- Enhanced `--version` banner displaying live VideoToolbox hardware acceleration availability.
- Graceful clean exit handling for `KeyboardInterrupt` (`Ctrl+C`, exit code `130`).

## [1.2.0] - 2026-08-24

### Changed
- Renamed project, CLI executable, and Python package to `slim-video` (`slim_video`).
- Updated persistent configuration file location to `~/.slim_video_config.json`.
- Updated persistent history file location to `~/.slim_video_history.json`.
- Standardized Conventional Commits documentation and CONTRIBUTING guidelines.

### Fixed
- Fixed runtime typing evaluation error on Python 3.9 using `Optional` and `eval-type-backport`.

## [1.1.0] - 2026-08-24

### Added
- 20-second sample estimation engine (`slim_video.estimator`) taking mid-point extracts to extrapolate full video compression ratio before batch processing.
- Automatic de-selection threshold (< 10% gain) for files where transcoding produces negligible space savings.
- Interactive terminal user interface (`slim_video.tree_selector`) with collapsible directory trees, checkbox selection, and real-time gain estimation badges.
- Environment & hardware diagnostics command `slim-video doctor` (`slim_video.doctor`) verifying dependencies, Apple Silicon VideoToolbox acceleration, and running a live transcode benchmark.
- Pydantic v2 data models and DTOs (`slim_video.models`, `slim_video.config`) with strict schema validation.
- Explicit configuration file management via `slim-video config` (`~/.slim_video_config.json`).
- Formatted summary text report generator (`transcode_report.txt`) saved in target folders.
- Native `uv` package manager support for fast installation and task execution.
- Strict static type checking with `mypy --strict`.
- GitHub Actions CI workflow with Conventional Commits checking, Ruff linting/formatting, Mypy, and multi-version Python testing (3.9–3.13).
- Automated GitHub release packaging workflow (`.github/workflows/release.yml`).

### Changed
- Refactored architecture into clean modular components with single responsibility.
- Replaced legacy data classes with Pydantic v2 `BaseModel`.
- Upgraded metadata with official author details (Alexandre Enouf).

### Fixed
- Terminal coordinate overflow in curses tree renderer on small screen viewports.
- Audio and subtitle stream mapping to guarantee lossless stream copy without re-encoding.

### Security
- Added safe quarantine mechanism moving source H.264 files to `_originals_to_delete/` instead of permanent deletion.

## [1.0.0] - 2026-08-20

### Added
- Initial release of hardware-accelerated H.264 to HEVC/x265 batch transcoder for Apple Silicon.
- VideoToolbox 10-bit color encoding (`p010le`) with spatial adaptive quantization (`spatial_aq`).
- Basic terminal file selector.
- Cumulative history tracking in `~/.slim_video_history.json`.

[Unreleased]: https://github.com/Boblebol/slim-video/compare/v1.5.2...HEAD
[1.5.2]: https://github.com/Boblebol/slim-video/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/Boblebol/slim-video/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/Boblebol/slim-video/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/Boblebol/slim-video/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/Boblebol/slim-video/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/Boblebol/slim-video/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/Boblebol/slim-video/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Boblebol/slim-video/releases/tag/v1.0.0
