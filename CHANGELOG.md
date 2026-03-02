# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-03-02

### Added
- Full `pytest` test suite for duration parsing, dataframe build, visualization, and CLI.
- Automatic coverage checks in `pytest` with a minimum 80% threshold.
- Explicit `python-dateutil` dependency for robust date/time handling.

### Changed
- Duration parsing migrated to `dateutil.relativedelta` for correct month/year handling (calendar-aware).
- `after <Label>` dependency resolution made more robust with explicit validation and errors.
- Improved `Start` field parsing to avoid warnings on non-date values.
- CLI version generation aligned with package metadata (`importlib.metadata`).
- Updated `pyproject.toml` to use `project.scripts` (replacing deprecated `tool.poetry.scripts`).

### Fixed
- Fixed CLI `--version` behavior (`expose_value=False`) to prevent unexpected arguments from being passed to `main`.

[1.1.0]: https://github.com/RomoloPoliti-INAF/Gantty/releases/tag/v1.1.0
