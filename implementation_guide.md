# OpenHands Dependency Reorganization: Technical Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the dependency reorganization plan outlined in `dependency_analysis.md`. It includes code examples, testing strategies, and specific implementation details.

## Step 1: Dependency Audit and Mapping

### 1.1 Create Dependency Mapping Script

```python
#!/usr/bin/env python3
"""
Script to analyze actual dependency usage in OpenHands codebase.
"""

import ast
import os
from collections import defaultdict
from pathlib import Path
import subprocess
import sys

def find_imports_in_file(filepath):
    """Extract all imports from a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])

        return imports
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return []

def analyze_dependencies():
    """Analyze which dependencies are actually used where."""
    usage_map = defaultdict(list)

    # Walk through all Python files in openhands/
    for root, dirs, files in os.walk('openhands'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                imports = find_imports_in_file(filepath)

                for imp in imports:
                    usage_map[imp].append(filepath)

    return usage_map

def get_pyproject_dependencies():
    """Extract dependencies from pyproject.toml."""
    try:
        import toml
        with open('pyproject.toml', 'r') as f:
            data = toml.load(f)

        deps = data['tool']['poetry']['dependencies']
        return list(deps.keys())
    except Exception as e:
        print(f"Error reading pyproject.toml: {e}")
        return []

if __name__ == "__main__":
    print("Analyzing dependency usage...")
    usage_map = analyze_dependencies()
    pyproject_deps = get_pyproject_dependencies()

    print("\n=== DEPENDENCY USAGE ANALYSIS ===")

    # Find unused dependencies
    unused_deps = []
    for dep in pyproject_deps:
        if dep not in usage_map and dep != 'python':
            unused_deps.append(dep)

    print(f"\nPotentially unused dependencies ({len(unused_deps)}):")
    for dep in sorted(unused_deps):
        print(f"  - {dep}")

    # Show usage by module
    print(f"\nDependency usage by location:")
    for dep, files in sorted(usage_map.items()):
        if dep in pyproject_deps:
            print(f"\n{dep}:")
            for file in sorted(set(files)):
                print(f"  - {file}")
```

### 1.2 Run Dependency Analysis Tools

```bash
# Install analysis tools
pip install deptry pydeps grimp pipreqs

# Run analysis
python dependency_analyzer.py > dependency_usage_report.txt

# Use deptry to find unused dependencies
deptry openhands --config pyproject.toml > deptry_report.txt

# Generate requirements from actual imports
pipreqs openhands --print > actual_requirements.txt
```

## Step 2: Code Refactoring for Optional Dependencies

### 2.1 Create Import Guard Utilities

```python
# openhands/utils/import_utils.py (enhance existing file)

import importlib
import warnings
from typing import Any, Optional, Dict, Set
from functools import lru_cache

class OptionalDependency:
    """Manages optional dependencies with helpful error messages."""

    def __init__(self, name: str, package: str, extra: str, purpose: str = ""):
        self.name = name
        self.package = package
        self.extra = extra
        self.purpose = purpose
        self._module: Optional[Any] = None
        self._checked = False

    @property
    def is_available(self) -> bool:
        """Check if the dependency is available."""
        if not self._checked:
            try:
                self._module = importlib.import_module(self.name)
                self._checked = True
            except ImportError:
                self._module = None
                self._checked = True
        return self._module is not None

    @property
    def module(self) -> Any:
        """Get the module, raising helpful error if not available."""
        if not self.is_available:
            raise ImportError(
                f"{self.name} is required {self.purpose}. "
                f"Install with: pip install {self.package}[{self.extra}]"
            )
        return self._module

    def require(self) -> Any:
        """Alias for module property."""
        return self.module

# Define optional dependencies
OPTIONAL_DEPS = {
    'docker': OptionalDependency(
        'docker', 'openhands-ai', 'runtime',
        'for Docker runtime support'
    ),
    'kubernetes': OptionalDependency(
        'kubernetes', 'openhands-ai', 'k8s',
        'for Kubernetes runtime support'
    ),
    'fastapi': OptionalDependency(
        'fastapi', 'openhands-ai', 'server',
        'for web server functionality'
    ),
    'browsergym': OptionalDependency(
        'browsergym', 'openhands-ai', 'browser',
        'for browser automation'
    ),
    'PyPDF2': OptionalDependency(
        'PyPDF2', 'openhands-ai', 'files',
        'for PDF file processing'
    ),
    'boto3': OptionalDependency(
        'boto3', 'openhands-ai', 'aws',
        'for AWS integration'
    ),
    'redis': OptionalDependency(
        'redis', 'openhands-ai', 'storage',
        'for Redis storage backend'
    ),
}

def get_optional_dependency(name: str) -> OptionalDependency:
    """Get an optional dependency manager."""
    if name not in OPTIONAL_DEPS:
        raise ValueError(f"Unknown optional dependency: {name}")
    return OPTIONAL_DEPS[name]

def check_optional_dependencies(required: Set[str]) -> Dict[str, bool]:
    """Check availability of multiple optional dependencies."""
    return {name: OPTIONAL_DEPS[name].is_available for name in required}

def require_dependencies(required: Set[str]) -> Dict[str, Any]:
    """Require multiple dependencies, raising error if any missing."""
    result = {}
    missing = []

    for name in required:
        dep = OPTIONAL_DEPS[name]
        if dep.is_available:
            result[name] = dep.module
        else:
            missing.append(dep)

    if missing:
        extras = set(dep.extra for dep in missing)
        raise ImportError(
            f"Missing required dependencies: {[dep.name for dep in missing]}. "
            f"Install with: pip install openhands-ai[{','.join(extras)}]"
        )

    return result
```

### 2.2 Refactor Runtime Modules

```python
# openhands/runtime/impl/docker/docker_runtime.py

from openhands.utils.import_utils import get_optional_dependency

# Replace direct import
# import docker

# With optional import
docker_dep = get_optional_dependency('docker')

class DockerRuntime(Runtime):
    """Docker-based runtime implementation."""

    def __init__(self, config: RuntimeConfig):
        # Check dependency at initialization
        self.docker = docker_dep.require()
        super().__init__(config)

        # Rest of initialization...
        self.client = self.docker.from_env()

    @classmethod
    def is_available(cls) -> bool:
        """Check if Docker runtime is available."""
        return docker_dep.is_available
```

```python
# openhands/runtime/impl/kubernetes/kubernetes_runtime.py

from openhands.utils.import_utils import get_optional_dependency

k8s_dep = get_optional_dependency('kubernetes')

class KubernetesRuntime(Runtime):
    """Kubernetes-based runtime implementation."""

    def __init__(self, config: RuntimeConfig):
        self.k8s = k8s_dep.require()
        super().__init__(config)

        # Initialize Kubernetes client
        self.k8s.config.load_incluster_config()

    @classmethod
    def is_available(cls) -> bool:
        """Check if Kubernetes runtime is available."""
        return k8s_dep.is_available
```

### 2.3 Refactor Server Modules

```python
# openhands/server/app.py

from openhands.utils.import_utils import get_optional_dependency

fastapi_dep = get_optional_dependency('fastapi')
uvicorn_dep = get_optional_dependency('uvicorn')

def create_app():
    """Create FastAPI application."""
    FastAPI = fastapi_dep.require().FastAPI

    app = FastAPI(
        title="OpenHands API",
        description="OpenHands Agent API",
        version="1.0.0"
    )

    # Rest of app setup...
    return app

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the OpenHands server."""
    uvicorn = uvicorn_dep.require()

    uvicorn.run(
        "openhands.server.app:create_app",
        host=host,
        port=port,
        factory=True
    )
```

### 2.4 Add Feature Detection

```python
# openhands/core/features.py

from openhands.utils.import_utils import OPTIONAL_DEPS
from typing import Dict, List

class FeatureManager:
    """Manages available features based on installed dependencies."""

    @classmethod
    def get_available_features(cls) -> Dict[str, bool]:
        """Get all available features."""
        return {
            'docker_runtime': OPTIONAL_DEPS['docker'].is_available,
            'kubernetes_runtime': OPTIONAL_DEPS['kubernetes'].is_available,
            'web_server': OPTIONAL_DEPS['fastapi'].is_available,
            'browser_automation': OPTIONAL_DEPS['browsergym'].is_available,
            'pdf_processing': OPTIONAL_DEPS['PyPDF2'].is_available,
            'aws_integration': OPTIONAL_DEPS['boto3'].is_available,
            'redis_storage': OPTIONAL_DEPS['redis'].is_available,
        }

    @classmethod
    def get_available_runtimes(cls) -> List[str]:
        """Get list of available runtime types."""
        runtimes = ['local']  # Always available

        if OPTIONAL_DEPS['docker'].is_available:
            runtimes.append('docker')

        if OPTIONAL_DEPS['kubernetes'].is_available:
            runtimes.append('kubernetes')

        return runtimes

    @classmethod
    def validate_config(cls, config: dict) -> List[str]:
        """Validate configuration against available features."""
        warnings = []

        runtime_type = config.get('runtime', {}).get('type', 'local')
        if runtime_type == 'docker' and not OPTIONAL_DEPS['docker'].is_available:
            warnings.append(
                "Docker runtime configured but docker not installed. "
                "Install with: pip install openhands-ai[runtime]"
            )

        if runtime_type == 'kubernetes' and not OPTIONAL_DEPS['kubernetes'].is_available:
            warnings.append(
                "Kubernetes runtime configured but kubernetes not installed. "
                "Install with: pip install openhands-ai[k8s]"
            )

        return warnings
```

## Step 3: Update pyproject.toml

### 3.1 Reorganize Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.12,<3.14"

# Core dependencies - always installed (includes all core packages)
# This includes: events, llm, runtime, controller, critic, agenthub,
# integrations, storage, security, memory, microagent, mcp, core, utils
litellm = "^1.74.3, !=1.64.4, !=1.67.*"
aiohttp = ">=3.9.0,!=3.11.13"
termcolor = "*"
toml = "*"
types-toml = "*"
python-dotenv = "*"
tenacity = ">=8.5,<10.0"
pydantic = "*"
python-json-logger = "^3.2.1"
prompt-toolkit = "^3.0.50"
jinja2 = "^3.1.3"
pathspec = "^0.12.1"
pyjwt = "^2.9.0"
python-frontmatter = "^1.1.0"
shellingham = "^1.5.4"
pyyaml = "^6.0.2"
bashlex = "^0.18"
zope-interface = "7.2"
protobuf = "^5.0.0,<6.0.0"
opentelemetry-api = "^1.33.1"
opentelemetry-exporter-otlp-proto-grpc = "^1.33.1"
libtmux = ">=0.37,<0.40"
psutil = "*"
anyio = "4.9.0"
dirhash = "*"
rapidfuzz = "^3.9.0"
whatthepatch = "^1.0.6"
deprecated = "*"
httpx-aiohttp = "^0.1.8"
pexpect = "*"  # Needed for core runtime functionality
fastmcp = "^2.5.2"  # Needed for core MCP functionality

# Optional dependencies for heavy/specialized features
docker = { version = "*", optional = true }
kubernetes = { version = "^33.1.0", optional = true }
fastapi = { version = "*", optional = true }
uvicorn = { version = "*", optional = true }
python-multipart = { version = "*", optional = true }
tornado = { version = "*", optional = true }
python-socketio = { version = "^5.11.4", optional = true }
sse-starlette = { version = "^2.1.3", optional = true }
browsergym-core = { version = "0.13.3", optional = true }
html2text = { version = "*", optional = true }
PyPDF2 = { version = "*", optional = true }
python-pptx = { version = "*", optional = true }
pylatexenc = { version = "*", optional = true }
python-docx = { version = "*", optional = true }
ipywidgets = { version = "^8.1.5", optional = true }
qtconsole = { version = "^5.6.1", optional = true }
jupyter_kernel_gateway = { version = "*", optional = true }
google-generativeai = { version = "*", optional = true }
google-api-python-client = { version = "^2.164.0", optional = true }
google-auth-httplib2 = { version = "*", optional = true }
google-auth-oauthlib = { version = "*", optional = true }
redis = { version = ">=5.2,<7.0", optional = true }
minio = { version = "^7.2.8", optional = true }
stripe = { version = ">=11.5,<13.0", optional = true }
google-cloud-aiplatform = { version = "*", optional = true }
anthropic = { version = "*", extras = ["vertex"], optional = true }
boto3 = { version = "*", optional = true }
pygithub = { version = "^2.5.0", optional = true }
openhands-aci = { version = "0.3.1", optional = true }
pythonnet = { version = "*", optional = true }
memory-profiler = { version = "^0.61.0", optional = true }
numpy = { version = "*", optional = true }
json-repair = { version = "*", optional = true }
joblib = { version = "*", optional = true }
e2b = { version = ">=1.0.5,<1.8.0", optional = true }
modal = { version = ">=0.66.26,<1.2.0", optional = true }
runloop-api-client = { version = "0.50.0", optional = true }
daytona = { version = "0.24.2", optional = true }
poetry = { version = "^2.1.2", optional = true }

[tool.poetry.extras]
# Main feature packages (these include the full packages)
cli = []  # CLI package included but no extra dependencies currently needed
resolver = []  # Resolver package included but no extra dependencies currently needed
server = ["fastapi", "uvicorn", "python-multipart", "tornado", "python-socketio", "sse-starlette"]

# Runtime environment support (optional heavy dependencies for core functionality)
docker = ["docker"]
kubernetes = ["kubernetes"]
browser = ["browsergym-core", "html2text"]

# File processing capabilities (optional dependencies for core functionality)
files = ["PyPDF2", "python-pptx", "pylatexenc", "python-docx"]

# Cloud integrations (optional dependencies for core functionality)
aws = ["boto3", "anthropic"]
google = ["google-generativeai", "google-api-python-client", "google-auth-httplib2", "google-auth-oauthlib", "google-cloud-aiplatform"]
azure = ["openhands-aci"]

# Storage backends (optional dependencies for core functionality)
storage = ["redis", "minio"]

# Development tools
dev = ["ipywidgets", "qtconsole", "jupyter_kernel_gateway"]
analysis = ["memory-profiler", "numpy", "json-repair", "joblib"]

# External runtimes
e2b = ["e2b"]
modal = ["modal"]
runloop = ["runloop-api-client"]
daytona = ["daytona"]

# Specialized features
payments = ["stripe"]
github = ["pygithub"]
dotnet = ["pythonnet"]

# Convenience combinations
local = ["docker", "files"]  # Local development with Docker and file processing
web = ["server", "browser", "files"]  # Web server with browser and file support
cloud = ["aws", "google", "azure", "storage"]  # All cloud integrations
full = ["cli", "resolver", "server", "docker", "kubernetes", "browser", "files",
       "aws", "google", "azure", "storage", "dev", "analysis", "e2b", "modal",
       "runloop", "daytona", "payments", "github", "dotnet"]
```

## Step 4: Testing Strategy

### 4.1 Create Test Matrix

```python
# tests/test_optional_dependencies.py

import pytest
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

EXTRAS_TO_TEST = [
    'runtime',
    'server',
    'browser',
    'files',
    'aws',
    'google',
    'k8s',
    'local',
    'web',
    'cloud'
]

IMPORT_TESTS = {
    'runtime': [
        'import openhands.runtime.impl.docker',
        'from openhands.runtime import get_runtime_cls',
    ],
    'server': [
        'import openhands.server.app',
        'from openhands.server.app import create_app',
    ],
    'browser': [
        'import openhands.runtime.browser',
        'from openhands.agenthub.browsing_agent import BrowsingAgent',
    ],
    'files': [
        'from openhands.runtime.plugins.agent_skills.file_reader import file_readers',
    ],
}

class TestOptionalDependencies:
    """Test that optional dependencies work correctly."""

    def test_core_import_without_extras(self):
        """Test that core OpenHands can be imported without any extras."""
        # Create a minimal virtual environment
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            venv.create(venv_path, with_pip=True)

            # Install only core package
            subprocess.run([
                str(venv_path / "bin" / "pip"), "install", "-e", "."
            ], check=True)

            # Test core import
            result = subprocess.run([
                str(venv_path / "bin" / "python"), "-c",
                "import openhands; print('Core import successful')"
            ], capture_output=True, text=True)

            assert result.returncode == 0
            assert "Core import successful" in result.stdout

    @pytest.mark.parametrize("extra", EXTRAS_TO_TEST)
    def test_extra_installation(self, extra):
        """Test that each extra can be installed and imported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "test_venv"
            venv.create(venv_path, with_pip=True)

            # Install with extra
            subprocess.run([
                str(venv_path / "bin" / "pip"), "install", "-e", f".[{extra}]"
            ], check=True)

            # Test imports if defined
            if extra in IMPORT_TESTS:
                for import_stmt in IMPORT_TESTS[extra]:
                    result = subprocess.run([
                        str(venv_path / "bin" / "python"), "-c", import_stmt
                    ], capture_output=True, text=True)

                    assert result.returncode == 0, f"Failed to import with {extra}: {result.stderr}"

    def test_feature_detection(self):
        """Test that feature detection works correctly."""
        from openhands.core.features import FeatureManager

        features = FeatureManager.get_available_features()
        assert isinstance(features, dict)
        assert 'docker_runtime' in features
        assert 'web_server' in features

        runtimes = FeatureManager.get_available_runtimes()
        assert isinstance(runtimes, list)
        assert 'local' in runtimes  # Always available

    def test_graceful_degradation(self):
        """Test that missing dependencies are handled gracefully."""
        from openhands.utils.import_utils import get_optional_dependency

        # Test with a dependency that's likely not installed
        dep = get_optional_dependency('kubernetes')

        if not dep.is_available:
            with pytest.raises(ImportError) as exc_info:
                dep.require()

            assert "kubernetes" in str(exc_info.value)
            assert "pip install" in str(exc_info.value)
```

### 4.2 Create CI Test Matrix

```yaml
# .github/workflows/test-extras.yml
name: Test Optional Dependencies

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test-extras:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        extra:
          - "core"  # No extras
          - "runtime"
          - "server"
          - "browser"
          - "files"
          - "local"
          - "web"
          - "all"

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ "${{ matrix.extra }}" = "core" ]; then
          pip install -e .
        else
          pip install -e .[${{ matrix.extra }}]
        fi

    - name: Test imports
      run: |
        python -c "import openhands; print('✓ Core import successful')"

        # Test specific functionality based on extra
        if [ "${{ matrix.extra }}" = "runtime" ] || [ "${{ matrix.extra }}" = "local" ] || [ "${{ matrix.extra }}" = "all" ]; then
          python -c "from openhands.runtime import get_runtime_cls; print('✓ Runtime import successful')"
        fi

        if [ "${{ matrix.extra }}" = "server" ] || [ "${{ matrix.extra }}" = "web" ] || [ "${{ matrix.extra }}" = "all" ]; then
          python -c "from openhands.server.app import create_app; print('✓ Server import successful')"
        fi

    - name: Run tests
      run: |
        python -m pytest tests/test_optional_dependencies.py -v
```

## Step 5: Documentation Updates

### 5.1 Update Installation Guide

```markdown
# Installation Guide

## Quick Start

For most users, install OpenHands with the features you need:

```bash
# Core installation (includes all essential packages)
pip install openhands-ai

# Add command-line interface
pip install openhands-ai[cli]

# Add web server and API
pip install openhands-ai[server]

# Add issue resolution functionality
pip install openhands-ai[resolver]

# For everything (current behavior)
pip install openhands-ai[full]
```

## Installation Options

### Core Installation
```bash
pip install openhands-ai
```
Includes all core packages: events, llm, runtime, controller, critic, agenthub, integrations, storage, security, memory, microagent, mcp, core, and utils.

### Optional Feature Packages

#### Main Features
```bash
# Command-line interface
pip install openhands-ai[cli]

# Issue resolution functionality
pip install openhands-ai[resolver]

# Web server and API
pip install openhands-ai[server]
```

#### Heavy Dependencies (for core functionality)
```bash
# Docker runtime support
pip install openhands-ai[docker]

# Kubernetes support
pip install openhands-ai[kubernetes]

# Browser automation
pip install openhands-ai[browser]

# Document processing (PDF, Word, PowerPoint)
pip install openhands-ai[files]
```

#### Cloud Integrations
```bash
# AWS integration (S3, Bedrock)
pip install openhands-ai[aws]

# Google Cloud integration
pip install openhands-ai[google]

# Azure integration
pip install openhands-ai[azure]

# All cloud providers
pip install openhands-ai[cloud]
```

#### Storage Backends
```bash
# Redis and Minio support
pip install openhands-ai[storage]
```

### Convenience Combinations
```bash
# Local development with Docker and file processing
pip install openhands-ai[local]

# Web server with browser and file support
pip install openhands-ai[web]

# All cloud integrations
pip install openhands-ai[cloud]

# Everything (same as current installation)
pip install openhands-ai[full]
```

### Development Installation
```bash
# For contributors
pip install openhands-ai[dev]

# For Jupyter notebook integration
pip install openhands-ai[dev]
```

## Troubleshooting

### Missing Dependency Errors

If you see an error like:
```
ImportError: docker is required for Docker runtime support.
Install with: pip install openhands-ai[runtime]
```

Install the suggested extra:
```bash
pip install openhands-ai[runtime]
```

### Checking Available Features

```python
from openhands.core.features import FeatureManager

# Check what features are available
features = FeatureManager.get_available_features()
print(features)

# Check available runtimes
runtimes = FeatureManager.get_available_runtimes()
print(runtimes)
```
```

### 5.2 Create Migration Guide

```markdown
# Migration Guide: Dependency Reorganization

## Overview

OpenHands has reorganized its dependencies to allow more flexible installations. This guide helps you migrate from the old installation method to the new extras-based approach.

## What Changed

### Before (v0.51.x and earlier)
```bash
pip install openhands-ai  # Installed everything
```

### After (v0.52.x and later)
```bash
pip install openhands-ai[extras]  # Install only what you need
```

## Migration Steps

### 1. Identify Your Usage

**If you use OpenHands locally with Docker:**
```bash
pip install openhands-ai[local]
```

**If you run the web server:**
```bash
pip install openhands-ai[web]
```

**If you deploy to cloud platforms:**
```bash
pip install openhands-ai[cloud]
```

**If you want everything (same as before):**
```bash
pip install openhands-ai[all]
```

### 2. Update Your Installation

```bash
# Uninstall old version
pip uninstall openhands-ai

# Install with appropriate extras
pip install openhands-ai[local]  # or whatever fits your use case
```

### 3. Update Scripts and Documentation

Update any installation scripts or documentation to use the new extras syntax.

## Backwards Compatibility

The `all` extra provides the same functionality as the previous full installation:

```bash
pip install openhands-ai[all]
```

## Common Issues

### "Module not found" errors

If you get import errors after upgrading, you may need additional extras:

```bash
# Error: No module named 'docker'
pip install openhands-ai[runtime]

# Error: No module named 'fastapi'
pip install openhands-ai[server]

# Error: No module named 'browsergym'
pip install openhands-ai[browser]
```

### Configuration warnings

OpenHands will warn you if your configuration requires features that aren't installed:

```
WARNING: Docker runtime configured but docker not installed.
Install with: pip install openhands-ai[runtime]
```

Follow the suggested installation command to resolve these warnings.
```

## Step 6: Validation and Testing

### 6.1 Create Validation Script

```python
#!/usr/bin/env python3
"""
Validation script for dependency reorganization.
"""

import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import List, Dict

def create_test_env() -> Path:
    """Create a temporary virtual environment."""
    tmpdir = tempfile.mkdtemp()
    venv_path = Path(tmpdir) / "test_venv"
    venv.create(venv_path, with_pip=True)
    return venv_path

def install_package(venv_path: Path, extras: List[str] = None) -> bool:
    """Install package with optional extras."""
    pip_path = venv_path / "bin" / "pip"

    if extras:
        package = f".[{','.join(extras)}]"
    else:
        package = "."

    try:
        subprocess.run([str(pip_path), "install", "-e", package],
                      check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def test_imports(venv_path: Path, imports: List[str]) -> Dict[str, bool]:
    """Test a list of import statements."""
    python_path = venv_path / "bin" / "python"
    results = {}

    for import_stmt in imports:
        try:
            subprocess.run([str(python_path), "-c", import_stmt],
                          check=True, capture_output=True)
            results[import_stmt] = True
        except subprocess.CalledProcessError:
            results[import_stmt] = False

    return results

def main():
    """Run validation tests."""
    test_cases = [
        {
            'name': 'Core Installation',
            'extras': [],
            'imports': [
                'import openhands',
                'from openhands.core.config import OpenHandsConfig',
                'from openhands.events.action import Action',
            ]
        },
        {
            'name': 'Runtime Extra',
            'extras': ['runtime'],
            'imports': [
                'import openhands',
                'from openhands.runtime.impl.docker import DockerRuntime',
            ]
        },
        {
            'name': 'Server Extra',
            'extras': ['server'],
            'imports': [
                'import openhands',
                'from openhands.server.app import create_app',
            ]
        },
        {
            'name': 'Local Combination',
            'extras': ['local'],
            'imports': [
                'import openhands',
                'from openhands.runtime.impl.docker import DockerRuntime',
                'from openhands.runtime.plugins.agent_skills.file_reader import file_readers',
            ]
        }
    ]

    print("🧪 Running dependency validation tests...\n")

    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")

        # Create test environment
        venv_path = create_test_env()

        # Install package
        if install_package(venv_path, test_case['extras']):
            print("  ✅ Installation successful")

            # Test imports
            results = test_imports(venv_path, test_case['imports'])

            for import_stmt, success in results.items():
                status = "✅" if success else "❌"
                print(f"  {status} {import_stmt}")
        else:
            print("  ❌ Installation failed")

        print()

if __name__ == "__main__":
    main()
```

This implementation guide provides a comprehensive roadmap for reorganizing OpenHands dependencies into optional extras. The approach balances user flexibility with maintainability, ensuring that users can install only what they need while maintaining backward compatibility.
