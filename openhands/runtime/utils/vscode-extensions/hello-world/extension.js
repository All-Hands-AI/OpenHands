const vscode = require('vscode');
const MemoryMonitor = require('./memory_monitor');

function activate(context) {
    // Create memory monitor instance
    const memoryMonitor = new MemoryMonitor();
    
    // Register the original hello world command
    let helloWorldCommand = vscode.commands.registerCommand('openhands-hello-world.helloWorld', function () {
        vscode.window.showInformationMessage('Hello from OpenHands!');
    });
    
    // Register memory monitor start command
    let startMonitorCommand = vscode.commands.registerCommand('openhands-hello-world.startMemoryMonitor', function () {
        memoryMonitor.start();
    });
    
    // Register memory monitor stop command
    let stopMonitorCommand = vscode.commands.registerCommand('openhands-hello-world.stopMemoryMonitor', function () {
        memoryMonitor.stop();
    });
    
    // Register memory details command
    let showMemoryDetailsCommand = vscode.commands.registerCommand('openhands-hello-world.showMemoryDetails', function () {
        memoryMonitor.showDetails();
    });
    
    // Add all commands to subscriptions
    context.subscriptions.push(helloWorldCommand);
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
