# VS Code Extension Build Configuration

The `build_vscode.py` script automatically builds the OpenHands VS Code extension during the Poetry build process. However, it intelligently skips the build in contexts where it's not needed to avoid issues and improve build performance.

## Automatic Skip Conditions

The script automatically skips building the VS Code extension in these scenarios:

1. **CLI-only installation contexts** (uvx, pipx, uv)
2. **Shallow git repositories** (common with package managers)
3. **Git repositories with invalid HEAD** (empty repos, etc.)
4. **CI/automated environments** (unless explicitly enabled)
5. **Missing or insufficient Node.js version** (< 18)

## Environment Variables

### SKIP_VSCODE_BUILD
Set to `1`, `true`, or `yes` to explicitly skip VS Code extension build:
```bash
SKIP_VSCODE_BUILD=1 poetry build
```

### BUILD_VSCODE_IN_CI
Set to `1`, `true`, or `yes` to force building in CI environments:
```bash
BUILD_VSCODE_IN_CI=1 poetry build
```

## Troubleshooting

### "fatal: bad revision 'HEAD'" Error
This error occurs when trying to build in git repositories without commits or in unusual states. The improved build script now handles this gracefully by:
- Detecting invalid git repository states
- Skipping VS Code build in problematic repositories
- Using pre-built extensions when available

### uvx Installation Issues
When installing via uvx, the build script automatically detects the CLI-only context and skips VS Code extension building to avoid issues with shallow repositories and missing development dependencies.

### Manual Override
To force building the VS Code extension in any context:
```bash
# Temporarily disable all skip conditions
python build_vscode.py
```

## Development vs Production

- **Development environment**: Full git repository → VS Code extension is built
- **Production/CLI installation**: Shallow repository or CLI tools → VS Code extension build is skipped
- **CI environment**: Skipped by default, can be enabled with `BUILD_VSCODE_IN_CI=1`
