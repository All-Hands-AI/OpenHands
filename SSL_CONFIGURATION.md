# SSL/TLS Configuration for Inspection Environments

This repository is configured to work in environments with TLS/SSL inspection (such as corporate networks with MITM proxies).

## Overview

The build system has been configured to bypass SSL certificate verification when installing Python dependencies. This is necessary because SSL inspection proxies replace legitimate certificates with self-signed certificates, causing verification failures.

## Configuration Files

### 1. `pip.conf`
Contains trusted-host configuration for pip:
- pypi.org
- pypi.python.org
- files.pythonhosted.org

### 2. `sitecustomize.py`
A Python module that globally disables SSL verification for all Python SSL connections. This file is automatically copied to Poetry's Python environment during the build process.

### 3. `Makefile`
The Makefile has been updated to:
- Configure Poetry to disable SSL verification for PyPI (`poetry config certificates.PyPI.cert false`)
- Copy `pip.conf` to user pip configuration directories
- Install `sitecustomize.py` to Poetry's site-packages
- Set environment variables to disable SSL verification during package installation

## Security Notice

**WARNING:** Disabling SSL verification removes an important security layer. This configuration should **ONLY** be used in:
- Controlled corporate environments with SSL inspection
- Development/testing environments with trusted networks
- Environments where the network is already secured by other means

**DO NOT** use this configuration:
- In production environments
- When connecting to untrusted networks
- When downloading packages from public internet without SSL inspection

## How It Works

1. When you run `make build`, the build system configures Poetry to skip SSL verification
2. Poetry downloads package metadata from PyPI without verifying certificates
3. Poetry downloads package files from files.pythonhosted.org without verifying certificates
4. The `sitecustomize.py` module ensures all Python SSL connections bypass verification
5. Pip (when used directly) respects the `pip.conf` trusted-host settings

## Troubleshooting

If you still encounter SSL errors:

1. Ensure Poetry configuration is set:
   ```bash
   poetry config --list | grep cert
   ```
   Should show: `certificates.PyPI.cert = false`

2. Verify sitecustomize.py is installed in Poetry's environment:
   ```bash
   POETRY_PYTHON=$(which poetry | xargs head -1 | cut -d'!' -f2)
   $POETRY_PYTHON -c "import site; print(site.getsitepackages()[0])"
   # Check if sitecustomize.py exists in that directory
   ```

3. Check that pip.conf is in the correct location:
   ```bash
   cat ~/.config/pip/pip.conf
   cat ~/.pip/pip.conf
   ```

## Reverting SSL Configuration

To restore normal SSL verification:

1. Remove Poetry SSL bypass:
   ```bash
   poetry config --unset certificates.PyPI.cert
   ```

2. Remove pip configuration:
   ```bash
   rm ~/.config/pip/pip.conf
   rm ~/.pip/pip.conf
   ```

3. Remove sitecustomize.py from Poetry's environment (if installed)
