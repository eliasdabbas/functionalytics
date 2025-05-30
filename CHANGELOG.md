# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2025-05-30

### Added
- Callable support for `extra_data` parameter in `log_this` decorator
- Functions can now be passed to `extra_data` which are executed at runtime to provide dynamic context data
- Graceful error handling for callable `extra_data` - exceptions are caught and logged as `<extra_data_error>` entries
- Comprehensive test coverage for callable `extra_data` functionality including edge cases


## [0.5.1] - 2025-05-26

### Fixed
- Fixed duplicate error logging where exceptions were being logged to both main log file and error log file
- Error logs now properly appear only in their designated location (error file or stderr) without duplication

## [0.5.0] - 2025-05-25

### Added
- `log_conditions` parameter to the `log_this` decorator to allow logging based on conditions in args/kwargs.

### Changed
- Unified log format from separate `Args: [...]` and `Kwargs: {...}` to single `Values: a=1 b='hello' c=42` format
- Discarded parameters now show as `param=discarded` instead of being completely hidden
- Default parameter values are now included in logs even when not explicitly passed
- Consistent error handling: `param_attrs` now raises `KeyError` for invalid parameter names (matching `log_conditions` behavior)

### Fixed
- Parameter logging now includes all runtime values including defaults, providing complete visibility into function calls

## [0.4.0] - 2025-05-22

### Added
- `error_file_path` parameter to the `log_this` decorator to allow logging error information when a function fails.

## [0.3.0] - 2025-05-22

### Added
- `extra_data` parameter to the `log_this` decorator to allow logging additional information.

## [0.2.0] - 2025-05-20

### Added
- `param_attrs` parameter for the ability to log attributes of parameters instead of the parameters themselves.
- `discard_params` parameter to not log parameter that might have large or unwieldy values (CSV files, images, long strings, etc.)
