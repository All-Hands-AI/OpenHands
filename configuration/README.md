# OpenHands Configuration

Configuration management utilities for OpenHands.

## Overview

This package provides configuration management utilities for the OpenHands project, including:

- Configuration file parsing and validation
- Environment variable management
- Settings schema definitions
- Configuration merging and inheritance

## Installation

This package uses `uv` as the package manager. To install dependencies:

```bash
uv sync
```

## Development

To install development dependencies:

```bash
uv sync --group dev
```

To run tests:

```bash
uv run pytest
```

To run linting:

```bash
uv run ruff check .
uv run black --check .
```

## Usage

```python
from openhands_configuration import ConfigManager

# Example usage will be added as the package develops
```

## License

MIT License - see LICENSE file for details.