# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-05-22

### Added
- `extra_data` parameter to the `log_this` decorator to allow logging additional information.

## [0.2.0] - 2025-05-20

### Added
- `param_attrs` parameter for the ability to log attributes of parameters instead of the parameters themselves.
- `discard_params` parameter to not log parameter that might have large or unwieldy values (CSV files, images, long strings, etc.)
