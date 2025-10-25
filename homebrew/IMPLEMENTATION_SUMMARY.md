# Homebrew Installation Implementation Summary

## Overview

This document summarizes the implementation of Homebrew installation support for the OpenHands CLI. The implementation makes it easier for macOS users to install and use OpenHands without needing to manually install Python ecosystem tools like `uv`.

## Solution Design

### Approach

We implemented a **Homebrew tap** within the OpenHands repository. This approach was chosen because:

1. **Flexibility**: Easy to update and maintain alongside the main codebase
2. **Integration**: Keeps everything in one repository
3. **Control**: We maintain full control over the formula and release process
4. **Simplicity**: Users can install with simple `brew install` commands

### Command Names

The implementation provides two command names:

- **`oh`** - Short, memorable command (primary/recommended)
  - Follows modern CLI tool patterns (like `gh` for GitHub)
  - Verified to not conflict with common macOS/Linux utilities
  - Easy to type and remember

- **`openhands`** - Full name (alternative)
  - Provides clarity for those who prefer explicit names
  - Useful for scripts and documentation

Both commands invoke the same CLI application.

## Files Created

### 1. `homebrew/openhands.rb`

The Homebrew formula that:
- Downloads the OpenHands repository
- Creates a Python 3.12 virtual environment
- Installs the openhands-cli package with all dependencies
- Creates wrapper scripts for both `oh` and `openhands` commands
- Provides helpful installation messages (caveats)
- Includes tests to verify installation

**Key Features:**
- Uses Python's pip for dependency resolution (automatic handling of transitive dependencies)
- Leverages Homebrew's virtualenv support for clean isolation
- Provides helpful post-installation messages about requirements (Docker, API keys)
- Includes macOS Gatekeeper security warning handling

### 2. `homebrew/README.md`

Comprehensive user documentation covering:
- Installation methods (tap, direct, local)
- Usage instructions
- Requirements (Docker, API keys)
- Troubleshooting common issues
- Update and uninstall procedures

### 3. `homebrew/DEVELOPMENT.md`

Developer documentation covering:
- Formula structure and architecture
- Testing procedures
- Version update process
- Publishing guidelines
- Debugging tips
- Future code signing considerations

### 4. `homebrew/IMPLEMENTATION_SUMMARY.md` (this file)

High-level overview of the implementation for maintainers and contributors.

### 5. Updated `README.md`

The main repository README now includes:
- Homebrew installation as **Option 1 (Recommended)** for macOS users
- Clear instructions for both installation methods
- Maintains existing installation options

## Installation Methods

### Method 1: Using the Tap (Recommended)

```bash
# Add the tap
brew tap All-Hands-AI/openhands https://github.com/All-Hands-AI/OpenHands.git

# Install
brew install openhands
```

### Method 2: Direct Installation

```bash
brew install https://raw.githubusercontent.com/All-Hands-AI/OpenHands/main/homebrew/openhands.rb
```

### Method 3: Local Development

```bash
cd /path/to/OpenHands
brew install --build-from-source ./homebrew/openhands.rb
```

## Technical Details

### Dependencies

The formula automatically handles:
- Python 3.12 (installed by Homebrew as a dependency)
- All Python packages from `openhands-cli/pyproject.toml`:
  - openhands-sdk
  - openhands-tools
  - prompt-toolkit
  - typer
  - All transitive dependencies

### Installation Process

1. Homebrew downloads the repository tarball
2. Creates an isolated Python 3.12 virtualenv
3. Changes to `openhands-cli` subdirectory
4. Runs `pip install` to install the package and dependencies
5. Creates wrapper scripts in Homebrew's bin directory
6. Sets executable permissions
7. Displays helpful caveats to the user

### Wrapper Scripts

Both `oh` and `openhands` are bash wrapper scripts that:
```bash
#!/bin/bash
exec "/path/to/libexec/bin/python" -m openhands_cli.simple_main "$@"
```

This approach:
- Ensures the correct Python interpreter is used
- Maintains the virtual environment isolation
- Passes all arguments to the CLI properly
- Works with both GUI and CLI modes

## macOS Security Considerations

### Gatekeeper Warnings

macOS may show security warnings for unsigned binaries. We handle this by:

1. **Documentation**: Clear instructions in the caveats and README
2. **User Options**:
   - System Settings > Privacy & Security > "Open Anyway"
   - Or: `xattr -d com.apple.quarantine $(which oh)`

### Future: Code Signing

For production releases, we can implement:
- Apple Developer account code signing
- Notarization with Apple
- This would eliminate Gatekeeper warnings

The process is documented in `DEVELOPMENT.md` for future implementation.

## Testing

### Pre-Release Testing

Before releasing a new version:

```bash
# Install locally
brew install --build-from-source ./homebrew/openhands.rb

# Test commands
oh --help
openhands --help
oh serve

# Run formula tests
brew test openhands

# Audit the formula
brew audit --new-formula ./homebrew/openhands.rb
```

### Command Conflict Check

We verified that `oh` doesn't conflict with:
- Common shell utilities (ls, cd, grep, etc.)
- Common development tools (git, make, npm, etc.)
- macOS-specific utilities (open, pbcopy, brew, etc.)
- Linux utilities (apt, systemctl, etc.)

Result: ✅ No conflicts found

## User Experience Improvements

### Before (with uv)

```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart shell
exec $SHELL

# Run OpenHands
uvx --python 3.12 --from openhands-ai openhands serve
```

### After (with Homebrew)

```bash
# Install
brew install openhands

# Run OpenHands
oh serve
```

### Benefits

1. **Fewer steps**: Single installation command
2. **Familiar**: Uses standard Homebrew workflow
3. **Shorter command**: `oh` vs long `uvx` command
4. **No Python knowledge needed**: Homebrew handles Python setup
5. **Easy updates**: `brew upgrade openhands`
6. **Clean uninstall**: `brew uninstall openhands`

## Maintenance

### Version Updates

When releasing a new version:

1. Update `version` in `openhands.rb`
2. Update `url` to point to the tagged release
3. Calculate and add SHA256 checksum
4. Test the installation
5. Users update with `brew upgrade openhands`

See `DEVELOPMENT.md` for detailed procedures.

### Dependency Updates

Python dependency changes in `openhands-cli/pyproject.toml` are automatically picked up by the formula since it uses pip for installation. No formula changes needed.

## Future Enhancements

### 1. Submit to Homebrew Core

For maximum visibility, we could submit to official Homebrew:
- Requires stable, tagged releases
- Must pass strict CI tests
- Broader reach to users

### 2. Code Signing

Implement Apple Developer code signing:
- Eliminates security warnings
- Better user experience
- Requires Apple Developer account

### 3. Binary Distribution

Instead of building from source:
- Host pre-built binaries
- Faster installation
- Requires hosting infrastructure

### 4. Linux Support

Create similar installation methods for Linux:
- Snap packages
- AppImage
- Debian/Ubuntu PPA
- RPM repositories

## Success Criteria

✅ Users can install with: `brew install openhands`
✅ Short command `oh` works and doesn't conflict
✅ Full command `openhands` also works
✅ Both CLI and GUI modes functional
✅ Clear documentation provided
✅ Troubleshooting guide available
✅ Developer documentation for maintenance
✅ Main README updated with Homebrew instructions

## Support

For issues or questions:
- GitHub Issues: https://github.com/All-Hands-AI/OpenHands/issues
- Documentation: https://docs.all-hands.dev
- Discord: https://discord.gg/ESHStjSjD4

## License

MIT License - Same as OpenHands project

---

**Implementation Date**: 2025-10-25
**Formula Version**: 1.0.2
**Minimum macOS**: 10.15 (Catalina)
**Python Version**: 3.12
