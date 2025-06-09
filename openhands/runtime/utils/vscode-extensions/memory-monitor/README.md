# OpenHands Memory Monitor

A VSCode extension for monitoring system and process memory usage in real-time.

## Features

- **Real-time Memory Monitoring**: Displays current memory usage in the status bar
- **Detailed Memory Information**: View detailed memory statistics in a graphical interface
- **Process Monitoring**: See top processes by memory usage
- **Memory Usage History**: Track memory usage over time with interactive charts
- **Cross-Platform Support**: Works on Windows, macOS, and Linux

## Usage

The extension automatically starts monitoring memory usage when VSCode is launched. You can interact with it in the following ways:

### Status Bar Indicator

A memory usage indicator is displayed in the status bar showing the current system memory usage percentage. Click on this indicator to open the detailed memory view.

### Commands

The following commands are available in the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`):

- **Start Memory Monitor**: Start monitoring memory usage
- **Stop Memory Monitor**: Stop monitoring memory usage
- **Show Memory Details**: Open the detailed memory view

## Detailed Memory View

The detailed memory view provides comprehensive information about:

1. **System Memory**: Total, used, and free memory
2. **Process Memory**: Memory usage of the VSCode extension host process
3. **Memory History**: Chart showing memory usage over time
4. **Top Processes**: List of processes using the most memory

## Development

This extension is part of the OpenHands project. To modify or extend it:

1. Make changes to the source files
2. Test the extension in a development VSCode instance
3. Package the extension for distribution

## License

This extension is licensed under the MIT license.
