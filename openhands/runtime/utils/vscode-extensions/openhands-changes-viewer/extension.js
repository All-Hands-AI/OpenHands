const vscode = require('vscode');
const { ChangesProvider } = require('./changes-provider');
const { GitService } = require('./git-service');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('OpenHands Changes Viewer is now active');

    // Initialize the Git service
    const gitService = new GitService();

    // Create the tree data provider for the changes view
    const changesProvider = new ChangesProvider(gitService);

    // Register the tree data provider for the changes view
    const treeView = vscode.window.createTreeView('openhands-changes-view', {
        treeDataProvider: changesProvider,
        showCollapseAll: true
    });

    // Register the refresh command
    let refreshCommand = vscode.commands.registerCommand('openhands-changes-viewer.refreshChanges', () => {
        changesProvider.refresh();
    });

    // Register the view diff command
    let viewDiffCommand = vscode.commands.registerCommand('openhands-changes-viewer.viewDiff', async (fileItem) => {
        if (fileItem) {
            const { path, status } = fileItem;
            
            try {
                const diff = await gitService.getDiff(path);
                
                // Create a temporary file for the diff
                const uri = vscode.Uri.parse(`untitled:${path}.diff`);
                
                // Determine if this is a new file, deleted file, or modified file
                let content = '';
                
                if (status === 'A') {
                    // New file - show only the new content
                    content = diff.modified;
                } else if (status === 'D') {
                    // Deleted file - show only the original content
                    content = diff.original;
                } else {
                    // For modified files, show a diff header
                    content = `--- a/${path}\n+++ b/${path}\n\n${diff.original}\n\n=== Modified ===\n\n${diff.modified}`;
                }
                
                // Create a new document with the diff content
                const edit = new vscode.WorkspaceEdit();
                edit.createFile(uri, { overwrite: true });
                await vscode.workspace.applyEdit(edit);
                
                const document = await vscode.workspace.openTextDocument(uri);
                const editor = await vscode.window.showTextDocument(document);
                
                // Insert the diff content
                const fullRange = new vscode.Range(
                    0, 0,
                    document.lineCount, 0
                );
                
                await editor.edit(editBuilder => {
                    editBuilder.replace(fullRange, content);
                });
                
                // Set the language mode to help with syntax highlighting
                await vscode.languages.setTextDocumentLanguage(document, getLanguageFromPath(path));
            } catch (error) {
                vscode.window.showErrorMessage(`Failed to show diff: ${error.message}`);
            }
        }
    });
    
    // Register the open changes view command
    let openChangesViewCommand = vscode.commands.registerCommand('openhands-changes-viewer.openChangesView', () => {
        vscode.commands.executeCommand('workbench.view.extension.openhands-changes');
    });

    // Open the changes view when the extension is activated
    vscode.commands.executeCommand('workbench.view.extension.openhands-changes');

    // Add commands to subscriptions
    context.subscriptions.push(refreshCommand);
    context.subscriptions.push(viewDiffCommand);
    context.subscriptions.push(openChangesViewCommand);
    context.subscriptions.push(treeView);

    // Auto-refresh the changes view every 10 seconds
    const intervalId = setInterval(() => {
        changesProvider.refresh();
    }, 10000);

    // Clean up the interval when the extension is deactivated
    context.subscriptions.push({ dispose: () => clearInterval(intervalId) });
}

/**
 * Get the language ID from a file path for syntax highlighting
 * @param {string} path 
 * @returns {string}
 */
function getLanguageFromPath(path) {
    const extension = path.split('.').pop().toLowerCase();
    
    const extensionMap = {
        'js': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescriptreact',
        'jsx': 'javascriptreact',
        'py': 'python',
        'java': 'java',
        'c': 'c',
        'cpp': 'cpp',
        'cs': 'csharp',
        'go': 'go',
        'rs': 'rust',
        'php': 'php',
        'rb': 'ruby',
        'md': 'markdown',
        'json': 'json',
        'html': 'html',
        'css': 'css',
        'scss': 'scss',
        'less': 'less',
        'xml': 'xml',
        'yaml': 'yaml',
        'yml': 'yaml',
        'sh': 'shellscript',
        'bash': 'shellscript',
        'txt': 'plaintext'
    };
    
    return extensionMap[extension] || 'plaintext';
}

function deactivate() {
    console.log('OpenHands Changes Viewer is now deactivated');
}

module.exports = {
    activate,
    deactivate
};