const vscode = require('vscode');
const MemoryMonitor = require('./memory_monitor');

function activate(context) {
    // Create memory monitor instance
    const memoryMonitor = new MemoryMonitor();

    // Store the context in the memory monitor
    memoryMonitor.context = context;

    // Register memory monitor start command
    let startMonitorCommand = vscode.commands.registerCommand('openhands-memory-monitor.startMemoryMonitor', function () {
        memoryMonitor.start();
    });

    // Register memory monitor stop command
    let stopMonitorCommand = vscode.commands.registerCommand('openhands-memory-monitor.stopMemoryMonitor', function () {
        memoryMonitor.stop();
    });

    // Register memory details command
    let showMemoryDetailsCommand = vscode.commands.registerCommand('openhands-memory-monitor.showMemoryDetails', function () {
        memoryMonitor.showDetails();
    });

    // Add all commands to subscriptions
    context.subscriptions.push(startMonitorCommand);
    context.subscriptions.push(stopMonitorCommand);
    context.subscriptions.push(showMemoryDetailsCommand);

    // Start memory monitoring by default
    memoryMonitor.start();
}

function deactivate() {
    // Clean up resources if needed
}

module.exports = {
    activate,
    deactivate
}
