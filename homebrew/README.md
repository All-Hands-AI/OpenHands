# OpenHands Homebrew Tap

This directory contains the Homebrew formula for installing OpenHands CLI on macOS.

## Installation

### Option 1: Install from the OpenHands tap (Recommended)

```bash
# Add the OpenHands tap
brew tap All-Hands-AI/openhands https://github.com/All-Hands-AI/OpenHands.git

# Install OpenHands CLI
brew install openhands
```

### Option 2: Install directly from the repository

```bash
# Install directly from the formula file
brew install --HEAD https://raw.githubusercontent.com/All-Hands-AI/OpenHands/main/homebrew/openhands.rb
```

### Option 3: Install from local clone

If you have cloned the repository locally:

```bash
cd /path/to/OpenHands
brew install --build-from-source ./homebrew/openhands.rb
```

## Usage

After installation, you can use OpenHands CLI with either:

```bash
# Short command (recommended)
oh

# Or full name
openhands
```

### Getting Started

1. **Start the CLI:**
   ```bash
   oh
   ```

2. **Get help:**
   ```bash
   oh --help
   ```

3. **Start the GUI server:**
   ```bash
   oh serve
   ```

4. **Resume a conversation:**
   ```bash
   oh --resume <conversation-id>
   ```

## Requirements

- macOS 10.15 or later
- Python 3.12 (automatically installed by Homebrew as a dependency)
- Docker Desktop or OrbStack (for full functionality)
- An LLM API key (OpenAI, Anthropic, etc.)

## Updating

To update to the latest version:

```bash
brew update
brew upgrade openhands
```

## Uninstalling

To remove OpenHands CLI:

```bash
brew uninstall openhands
```

## Troubleshooting

### macOS Security Warning

On first run, macOS may show a security warning about an application from an unidentified developer. To resolve this:

1. Go to **System Settings** > **Privacy & Security**
2. Scroll down to find the message about OpenHands being blocked
3. Click **"Open Anyway"**

Alternatively, you can run this command to remove the quarantine attribute:

```bash
xattr -d com.apple.quarantine $(which oh)
xattr -d com.apple.quarantine $(which openhands)
```

### Command Not Found

If the `oh` or `openhands` command is not found after installation, try:

```bash
# Restart your shell
exec $SHELL

# Or reload your shell configuration
source ~/.zshrc  # For zsh
source ~/.bashrc # For bash
```

### Python Version Issues

If you encounter Python version issues, ensure you're using Python 3.12:

```bash
# Check Python version
python3.12 --version

# If missing, install via Homebrew
brew install python@3.12
```

### Installation Fails

If the installation fails, try:

```bash
# Clean up and reinstall
brew uninstall openhands
brew cleanup
brew install openhands
```

## Development

### Testing Changes Locally

If you're developing the formula:

```bash
# Test installation
brew install --build-from-source --verbose --debug ./homebrew/openhands.rb

# Test the formula
brew test openhands

# Audit the formula
brew audit --new-formula ./homebrew/openhands.rb
```

### Formula Structure

The formula:
- Downloads the OpenHands repository
- Creates a Python virtual environment
- Installs the openhands-cli package with all dependencies
- Creates wrapper scripts for `oh` and `openhands` commands
- Sets up proper permissions

## Contributing

If you find issues with the Homebrew formula or have suggestions for improvement, please:

1. Open an issue at https://github.com/All-Hands-AI/OpenHands/issues
2. Submit a pull request with your proposed changes

## License

MIT License - See the main repository LICENSE file for details.

## Support

For help and support:
- Documentation: https://docs.all-hands.dev
- GitHub Issues: https://github.com/All-Hands-AI/OpenHands/issues
- Discord: https://discord.gg/ESHStjSjD4
