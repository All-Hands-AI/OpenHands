const vscode = require('vscode');

/**
 * Checks if the URL contains the goto=terminal query parameter and opens a terminal if it does
 */
function checkUrlAndOpenTerminal() {
    // Get the current URL from the environment
    const url = process.env.VSCODE_BROWSER_URL;
    
    if (url && url.includes('?goto=terminal') || url && url.includes('&goto=terminal')) {
        // Open a new terminal
        vscode.window.createTerminal().show();
        vscode.window.showInformationMessage('Terminal opened automatically based on URL parameter');
    }
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    // Check URL on activation
    checkUrlAndOpenTerminal();
    
    // Register a command that can be called manually if needed
    let disposable = vscode.commands.registerCommand('openhands-goto-terminal.openTerminal', function () {
        vscode.window.createTerminal().show();
    });
    
    context.subscriptions.push(disposable);
    
    // Also listen for URI changes in case the user navigates within the editor
    context.subscriptions.push(
        vscode.window.onDidChangeWindowState(() => {
            checkUrlAndOpenTerminal();
        })
    );
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
}