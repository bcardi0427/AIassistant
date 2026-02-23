# Changelog

All notable changes to the AI Configuration Agent add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.22] - 2026-02-23

### Added
- Added `list_directory` tool: The AI can now explicitly browse the configuration filesystem, including virtual paths like `addon_configs/`. This provides a fail-safe way to find files when search fails.
- Updated System Prompt: Added instructions for the AI on how to use `list_directory` to discover add-on slugs and configuration files.

### Improved
- Re-engineered `search_config_files`: 
    - Switched to `os.walk` for guaranteed recursive discovery (fixing issues where some depth levels were skipped).
    - Massive increase in search limits: Now returns up to 500 files and allows up to 32KB of content per file.
    - Improved hidden file/directory pruning for better performance in large repositories.

## [0.9.21] - 2026-02-23

### Fixed
- Significantly improved the configuration search tool:
    - Increased result limit from 50 to 100 files to prevent skipping relevant configs in large setups.
    - Increased per-file content limit from 2KB to 16KB, allowing full review of complex YAML files (like Frigate or Zigbee2MQTT).
    - Prioritized `.yaml` and `.yml` files in search results so they appear above entity registry JSONs.
    - Improved hidden file detection to correctly handle absolute paths and custom Home Assistant installation directories.

## [0.9.20] - 2026-02-23

### Added
- Added support for searching and editing `.json` configuration files in both main and add-on configuration directories.

### Fixed
- Improved security filtering: Hidden files (starting with `.`) and internal directories (like `.storage`) are now automatically excluded from searches.
- Expanded exclusion list to include `secrets.json`.

## [0.9.19] - 2026-02-23

### Fixed
- Fixed environment variable mapping for the add-on configuration directory (aligned `ADDONS_DIR` between `run.sh` and `main.py`).
- Normalized virtual filesystem paths to use forward slashes consistently across all operating systems.

## [0.9.18] - 2026-02-23

### Fixed
- Enhanced `addon_configs/` search to support `.yml` file extensions.
- Fixed glob pattern searching for the virtual `addon_configs/` path.

## [0.9.17] - 2026-02-23

### Added
- Implemented support for the `addon_configs/` directory.
- Added a virtual file system bridge for search and editing of individual add-on configurations.
- Added `ADDONS_DIR` environment variable support (defaulting to `/addon_configs`).

## [0.9.16] - 2021-02-21

### Added
- Implemented comprehensive Lovelace dashboard management.
- Added new WebSocket API methods for listing, creating, updating, and deleting dashboards.
- Introduced virtual file paths for dashboard metadata (`dashboards/{url_path}.json`) and layout configurations (`lovelace/{url_path}.yaml`).

## [0.9.15] - 2026-02-11

### Fixed
- Sync versions and force HACS update.

## [0.9.14] - 2026-02-11

### Renamed
- Renamed project to **AIassistant** for personal HACS distribution.
- Updated all internal domains, paths, and branding.
- This is a breaking change; users must reinstall the integration.

## [0.1.0] - 2025-10-26

### Initial Version

Initial version of the AI Configuration Agent add-on

## [0.1.1] - 2025-10-26

Enhanced API and UI to use streaming responses to provide
faster feedback to the frontend as queries are processed involving
tools.

Added tool call results (and tool calls) into the chat history UI.

## [0.1.2] - 2025-10-26

Refactored API to use websockets as streaming responses was
not working properly.

## [0.1.3] - 2025-10-27

Moved system prompt into configuration options and improved prompt.

## [0.1.4] - 2025-10-27

Moved system prompt into config file as full system prompt in options was breaking HA.

## [0.1.5] - 2025-10-28

General bug fixes and improvements.

## [0.1.6] - 2025-10-28

Add prompt caching support for models that support it (currently only Gemini and Claude)

## [0.1.7] - 2025-10-28

Prevent leaking secrets to LLMs

## [0.1.8] - 2025-10-28

Import and export conversation history

## [0.1.9] - 2025-10-28

Added configurable temperature parameter for LLM calls. You can now specify the temperature (0.0-2.0) in the add-on configuration to control the randomness of the AI's responses. When not specified, the LLM provider's default temperature is used

## [0.1.10] - 2025-10-30

Made cache control configurable and added token usage tracking

## [0.1.11] - 2025-10-31

Enhanced search functionality to support file path patterns. When search_pattern starts with "/", it's treated as a glob pattern and only searches actual files (skipping virtual entities/devices/areas). Example: `/packages/*.yaml` will match all YAML files in the packages directory.

## [0.2.0] - 20205-11-01

Converted to support installation via HACS as custom component as well as add-on installation.