# CLI Editor Modes

OpenHands CLI supports two editor modes for command-line input:

## Editor Modes

### Emacs Mode (Default)
By default, OpenHands CLI uses **emacs-style key bindings** for command input. This provides familiar shortcuts for users accustomed to emacs or bash default behavior.

### Vi Mode
OpenHands also supports **vi-style key bindings** for users who prefer vim-like navigation and editing.

## Activation

### Command Line
To enable vi mode, use the `--vi-mode` flag:

```bash
# Enable vi-style key bindings
poetry run openhands cli --vi-mode

# Or with a task
poetry run openhands cli --vi-mode --task "Create a Python script"
```

### Configuration File
You can also enable vi mode in your `config.toml` file:

```toml
[cli]
vi_mode = true
```

## Key Bindings

### Emacs Mode (Default)
- Standard bash/emacs key bindings
- `Ctrl+A` - Beginning of line
- `Ctrl+E` - End of line
- `Ctrl+K` - Kill to end of line
- And other standard emacs shortcuts

### Vi Mode
- Vi-style navigation and editing
- `Esc` - Enter command mode
- `i` - Enter insert mode
- `h/j/k/l` - Navigation in command mode
- And other standard vi shortcuts

## Examples

```bash
# Use default emacs mode
poetry run openhands cli

# Use vi mode
poetry run openhands cli --vi-mode

# Use vi mode with specific task
poetry run openhands cli --vi-mode --task "Debug this Python code"
```

The editor mode only affects the command-line input interface and does not change OpenHands' core functionality.