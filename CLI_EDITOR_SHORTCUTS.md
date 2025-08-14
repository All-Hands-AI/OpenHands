# CLI Editor Shortcuts

OpenHands CLI now supports enhanced editor shortcuts for improved command-line editing experience. You can choose between Emacs-style and Vi-style key bindings.

## Features

### Editor Modes

- **Emacs Mode**: Comprehensive Emacs-style key bindings (default)
- **Vi Mode**: Vi/Vim-style modal editing using prompt_toolkit's built-in support
- **Auto Mode**: Automatically detects your preferred editor from the `$EDITOR` environment variable

### Command Line Options

```bash
# Explicitly set editor mode
openhands cli --editor-mode emacs
openhands cli --editor-mode vi
openhands cli --editor-mode auto

# Backward compatibility (deprecated)
openhands cli --vi-mode
```

### Configuration File

Add to your `config.toml`:

```toml
[cli]
editor_mode = "emacs"  # or "vi" or "auto"
vi_mode = false        # deprecated, use editor_mode instead
```

## Emacs Mode Key Bindings

### Cursor Movement
- `Ctrl+A`: Move to beginning of line
- `Ctrl+E`: Move to end of line
- `Ctrl+F`: Move forward one character
- `Ctrl+B`: Move backward one character
- `Alt+F`: Move forward one word
- `Alt+B`: Move backward one word

### Text Deletion
- `Ctrl+D`: Delete character at cursor
- `Ctrl+H`: Delete character before cursor (backspace)
- `Ctrl+K`: Kill (cut) from cursor to end of line
- `Ctrl+U`: Kill (cut) from cursor to beginning of line
- `Alt+D`: Kill word forward
- `Ctrl+W`: Kill word backward

### Text Manipulation
- `Ctrl+Y`: Yank (paste) killed text
- `Ctrl+T`: Transpose characters
- `Alt+T`: Transpose words
- `Alt+U`: Uppercase word
- `Alt+L`: Lowercase word
- `Alt+C`: Capitalize word

### Other
- `Ctrl+L`: Clear screen
- `Ctrl+_`: Undo last edit

## Vi Mode

Vi mode provides modal editing similar to Vim:

- **Insert Mode**: Normal text input
- **Command Mode**: Navigation and editing commands
- Press `Esc` to enter command mode
- Press `i`, `a`, `o`, etc. to enter insert mode

Vi mode uses prompt_toolkit's comprehensive built-in Vi support, providing familiar Vim-like editing experience.

## Auto-Detection

When `editor_mode = "auto"`, OpenHands automatically detects your preferred editor:

- If `$EDITOR` contains `vi`, `vim`, or `nvim`: Uses Vi mode
- Otherwise: Uses Emacs mode

Examples:
```bash
export EDITOR=vim      # → Vi mode
export EDITOR=nvim     # → Vi mode
export EDITOR=nano     # → Emacs mode
export EDITOR=code     # → Emacs mode
```

## Backward Compatibility

The old `--vi-mode` flag and `vi_mode` config option are still supported but deprecated:

```bash
# Still works (deprecated)
openhands cli --vi-mode

# Preferred
openhands cli --editor-mode vi
```

## Implementation Details

### Key Components

1. **CLIConfig** (`openhands/core/config/cli_config.py`):
   - `editor_mode`: New field for editor mode selection
   - `get_effective_editor_mode()`: Resolves auto mode
   - `is_vi_mode()`: Backward compatibility method

2. **Editor Bindings** (`openhands/cli/editor_bindings.py`):
   - `create_emacs_key_bindings()`: Comprehensive Emacs shortcuts
   - `create_vi_key_bindings()`: Vi mode setup (uses built-in support)
   - `create_enhanced_key_bindings()`: Factory function

3. **TUI Integration** (`openhands/cli/tui.py`):
   - Enhanced `create_prompt_session()` with editor mode support
   - Multiline input handling with consistent key bindings

4. **CLI Arguments** (`openhands/core/config/arg_utils.py`):
   - `--editor-mode`: New primary option
   - `--vi-mode`: Deprecated compatibility option

### Testing

Run the test suite:
```bash
python -m pytest tests/unit/test_cli_editor_shortcuts.py -v
```

Or run the comprehensive test script:
```bash
python test_final.py
```

## Migration Guide

### From vi_mode to editor_mode

**Old configuration:**
```toml
[cli]
vi_mode = true
```

**New configuration:**
```toml
[cli]
editor_mode = "vi"
```

**Command line:**
```bash
# Old (still works)
openhands cli --vi-mode

# New (preferred)
openhands cli --editor-mode vi
```

### Benefits of New System

1. **More Flexible**: Three modes instead of just on/off
2. **Auto-Detection**: Respects your `$EDITOR` preference
3. **Enhanced Emacs Support**: Comprehensive key bindings
4. **Better Vi Support**: Uses prompt_toolkit's full Vi implementation
5. **Future-Proof**: Extensible for additional editor modes

## Troubleshooting

### Key Bindings Not Working

1. Check your terminal's key binding conflicts
2. Verify your editor mode setting:
   ```bash
   openhands cli --editor-mode emacs  # or vi
   ```

### Auto-Detection Issues

1. Check your `$EDITOR` environment variable:
   ```bash
   echo $EDITOR
   ```

2. Override with explicit mode:
   ```bash
   openhands cli --editor-mode emacs
   ```

### Vi Mode Not Responsive

1. Make sure you're in the correct mode (press `Esc` for command mode)
2. Try explicit Vi mode:
   ```bash
   openhands cli --editor-mode vi
   ```

## Contributing

To extend the editor shortcuts:

1. Add new key bindings to `editor_bindings.py`
2. Update tests in `test_cli_editor_shortcuts.py`
3. Update this documentation

The system is designed to be extensible for future editor modes (e.g., nano-style, custom modes).