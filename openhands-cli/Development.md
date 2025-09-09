# Development Guide

Detailed guidance for contributors working on the OpenHands CLI.

## 1) Managing dependencies with Poetry/uv

This repo includes both pyproject sections for hatch/uv and Poetry for compatibility.

- Add a runtime dependency (using uv):
  ```bash
  uv add <package>
  ```
- Add a dev dependency (linters, build tools, etc.):
  ```bash
  uv add --dev <package>
  ```
- Sync environment:
  ```bash
  uv sync --extra dev
  ```

If you use Poetry instead of uv:
```bash
poetry add <package>
poetry add --group dev <package>
poetry install
```

Commit the updated pyproject.toml (and lockfile if applicable) with your change.

## 2) Packaging with PyInstaller: spec file tips

PyInstaller uses a spec file (openhands-cli.spec) to describe what to include in the binary.
Two common knobs when something is missing in the built executable:

- hiddenimports: Python modules that PyInstaller fails to detect automatically.
  Use when imports are dynamic or optional.
  Example in spec:
  ```python
  hiddenimports=[
      'openhands_cli.tui',
      'openhands_cli.pt_style',
      *collect_submodules('prompt_toolkit'),
      *collect_submodules('openhands.core'),
      *collect_submodules('openhands.tools'),
  ]
  ```

- datas (a.k.a. data files): Non-Python files required at runtime (templates, config, etc.).
  Use collect_data_files to include them.
  Example in spec:
  ```python
  datas=[
      *collect_data_files('tiktoken'),
      *collect_data_files('openhands.core.agent.codeact_agent', includes=['prompts/*.j2']),
  ]
  ```

Differences:
- hiddenimports is for modules to be packaged as bytecode.
- datas is for external resource files copied into the bundle.

If a library fails at runtime with "ModuleNotFoundError" inside the binary, add it to hiddenimports.
If a library complains about missing template/config/resource files, add those paths to datas.

## 3) Build locally and test

- Quick build (recommended):
  ```bash
  ./build.sh --install-pyinstaller
  ```
  This ensures PyInstaller is present via uv and then runs build.py.

- Manual build:
  ```bash
  uv add --dev pyinstaller
  uv run pyinstaller openhands-cli.spec --clean
  ```

- Test the binary:
  ```bash
  ./dist/openhands-cli            # macOS/Linux
  # or dist/openhands-cli.exe     # Windows
  ```

If the binary fails to start:
- Run the Python entrypoint to confirm the app itself works:
  ```bash
  uv run openhands-cli
  ```
- Re-run build with --no-clean to inspect build artifacts, or add more hiddenimports/datas.

## 4) Linting and formatting

- Run all pre-commit hooks:
  ```bash
  make lint
  ```
- Format code:
  ```bash
  make format
  ```

## 5) Notes on agent credentials

To actually converse with a model, export one of the supported keys before running the CLI/binary:
```bash
export OPENAI_API_KEY=...   # or
export LITELLM_API_KEY=...
```
