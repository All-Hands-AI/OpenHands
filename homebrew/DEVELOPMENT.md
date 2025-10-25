# Homebrew Formula Development Guide

This guide provides instructions for maintaining and testing the OpenHands Homebrew formula.

## Formula Structure

The `openhands.rb` formula:
- Downloads the OpenHands repository source
- Creates a Python 3.12 virtual environment
- Installs the openhands-cli package with all dependencies using pip
- Creates two wrapper scripts:
  - `oh` - Short command for quick access
  - `openhands` - Full name for clarity

## Testing the Formula Locally

### Prerequisites

- macOS with Homebrew installed
- Git
- Basic understanding of Homebrew formula development

### Test Installation

1. **Install from local formula:**
   ```bash
   cd /path/to/OpenHands
   brew install --build-from-source --verbose ./homebrew/openhands.rb
   ```

2. **Test the installed commands:**
   ```bash
   # Check if commands exist
   which oh
   which openhands

   # Test help output
   oh --help
   openhands --help

   # Test version
   oh --version
   ```

3. **Run the formula tests:**
   ```bash
   brew test openhands
   ```

4. **Audit the formula:**
   ```bash
   brew audit --new-formula ./homebrew/openhands.rb
   ```

### Uninstall for Testing

```bash
brew uninstall openhands
brew cleanup
```

## Updating the Formula

### Version Updates

When releasing a new version:

1. Update the `version` field in `openhands.rb`:
   ```ruby
   version "1.0.3"  # New version
   ```

2. If using a tagged release (recommended for production), update the `url`:
   ```ruby
   url "https://github.com/All-Hands-AI/OpenHands/archive/refs/tags/v1.0.3.tar.gz"
   ```

3. Calculate and update the SHA256 checksum:
   ```bash
   # Download the tarball
   curl -L https://github.com/All-Hands-AI/OpenHands/archive/refs/tags/v1.0.3.tar.gz -o openhands.tar.gz

   # Calculate SHA256
   shasum -a 256 openhands.tar.gz
   ```

4. Add the `sha256` field to the formula:
   ```ruby
   url "https://github.com/All-Hands-AI/OpenHands/archive/refs/tags/v1.0.3.tar.gz"
   sha256 "your-calculated-sha256-here"
   ```

### Dependency Updates

If Python dependencies change in `openhands-cli/pyproject.toml`, the formula will automatically pick them up since it uses pip to install the package. No formula changes are needed unless:
- The Python version requirement changes
- New system-level dependencies are needed

## Publishing the Formula

### Using as a Tap

Users can install from the tap:

```bash
# Add the tap (only needed once)
brew tap All-Hands-AI/openhands https://github.com/All-Hands-AI/OpenHands.git

# Install
brew install openhands

# Update
brew update
brew upgrade openhands
```

### Submitting to Homebrew Core (Optional)

For wider distribution, you can submit to Homebrew/homebrew-core:

1. Fork https://github.com/Homebrew/homebrew-core
2. Add the formula to `Formula/o/openhands.rb`
3. Follow Homebrew's contribution guidelines
4. Submit a pull request

**Requirements for Homebrew Core:**
- Formula must use stable, tagged releases (not `main` branch)
- Must pass all Homebrew CI tests
- Project should be relatively stable and well-maintained
- Must follow Homebrew formula style guidelines

## Common Issues and Solutions

### Issue: Installation fails with Python dependency errors

**Solution:** Ensure the `openhands-cli/pyproject.toml` has correct dependency specifications. The formula relies on pip to resolve all dependencies.

### Issue: Commands not found after installation

**Solution:**
```bash
# Restart shell
exec $SHELL

# Or check Homebrew paths
brew doctor
```

### Issue: macOS Gatekeeper blocks execution

**Solution:** This is expected for unsigned binaries. Users can:
1. Go to System Settings > Privacy & Security > Click "Open Anyway"
2. Or run: `xattr -d com.apple.quarantine $(which oh)`

### Issue: Formula fails brew audit

**Solution:**
```bash
# Run audit to see specific issues
brew audit --strict --online ./homebrew/openhands.rb

# Common fixes:
# - Ensure proper formatting (2 spaces, no tabs)
# - Add missing license field
# - Fix URL format
# - Add proper test section
```

## Testing Different Installation Methods

### Method 1: Direct from GitHub

```bash
brew install https://raw.githubusercontent.com/All-Hands-AI/OpenHands/main/homebrew/openhands.rb
```

### Method 2: From Tap

```bash
brew tap All-Hands-AI/openhands https://github.com/All-Hands-AI/OpenHands.git
brew install openhands
```

### Method 3: Local Development

```bash
cd /path/to/OpenHands
brew install --build-from-source ./homebrew/openhands.rb
```

## Debugging

Enable verbose output:
```bash
brew install --verbose --debug ./homebrew/openhands.rb
```

Check installation logs:
```bash
brew info openhands
brew list openhands
```

View formula code:
```bash
brew cat openhands
```

## Code Signing (Future)

For production releases, consider code signing the binaries:

1. Get an Apple Developer account
2. Create a Developer ID Application certificate
3. Sign the binaries:
   ```bash
   codesign --sign "Developer ID Application: Your Name" /path/to/binary
   ```
4. Notarize with Apple:
   ```bash
   xcrun notarytool submit /path/to/binary --apple-id your@email.com
   ```

This removes the Gatekeeper warning for users.

## Resources

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Python for Formula Authors](https://docs.brew.sh/Python-for-Formula-Authors)
- [Homebrew Acceptable Formulae](https://docs.brew.sh/Acceptable-Formulae)
- [Homebrew Style Guide](https://docs.brew.sh/Formula-Cookbook#style)

## Maintenance Checklist

- [ ] Test formula installs correctly
- [ ] Verify both `oh` and `openhands` commands work
- [ ] Check help output displays correctly
- [ ] Run `brew audit` and fix any issues
- [ ] Update version number for releases
- [ ] Update SHA256 for tagged releases
- [ ] Test on clean macOS system if possible
- [ ] Update documentation if CLI usage changes
