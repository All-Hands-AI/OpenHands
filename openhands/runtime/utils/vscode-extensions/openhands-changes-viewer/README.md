# OpenHands Changes Viewer

A VSCode extension for viewing changes made by the OpenHands agent.

## Features

- Shows a list of changed files in the workspace
- Displays the status of each file (Added, Modified, Deleted)
- Allows viewing the diff of each file
- Automatically refreshes the list of changes every 10 seconds
- Opens automatically at VSCode startup

## Usage

The extension adds a new view container to the activity bar with a "Changes" icon. Click on it to see the list of changed files.

- Click on a file to view its diff
- Click the refresh button to manually refresh the list of changes
- Right-click on a file to see additional options

## Requirements

- VSCode 1.98.2 or higher
- Git must be installed and available in the PATH

## Extension Settings

This extension does not contribute any settings.

## Known Issues

- The diff view is basic and does not support all the features of the built-in diff editor
- The extension may not work correctly in workspaces without Git

## Release Notes

### 0.1.0

Initial release of OpenHands Changes Viewer