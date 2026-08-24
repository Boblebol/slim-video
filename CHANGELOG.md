# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-08-24

### Added
- 20-second sample estimation engine (`hevc_cli.estimator`) taking mid-point extracts to extrapolate full video compression ratio before batch processing.
- Automatic de-selection threshold (< 10% gain) for files where transcoding produces negligible space savings.
- Interactive terminal user interface (`hevc_cli.tree_selector`) with collapsible directory trees, checkbox selection, and real-time gain estimation badges.
- Environment & hardware diagnostics command `hevc-cli doctor` (`hevc_cli.doctor`) verifying dependencies, Apple Silicon VideoToolbox acceleration, and running a live transcode benchmark.
- Pydantic v2 data models and DTOs (`hevc_cli.models`, `hevc_cli.config`) with strict schema validation.
- Explicit configuration file management via `hevc-cli config` (`~/.hevc_cli_config.json`).
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
- Cumulative history tracking in `~/.hevc_cli_history.json`.

[Unreleased]: https://github.com/Boblebol/slim-video/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/Boblebol/slim-video/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Boblebol/slim-video/releases/tag/v1.0.0
