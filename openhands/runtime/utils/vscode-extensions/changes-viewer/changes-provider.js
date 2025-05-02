const vscode = require('vscode');

/**
 * TreeDataProvider for the Changes view
 */
class ChangesProvider {
    /**
     * @param {import('./git-service').GitService} gitService 
     */
    constructor(gitService) {
        this.gitService = gitService;
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
    }

    /**
     * Refresh the tree view
     */
    refresh() {
        this._onDidChangeTreeData.fire();
    }

    /**
     * Get the tree item for the given element
     * @param {any} element 
     * @returns {vscode.TreeItem}
     */
    getTreeItem(element) {
        return element;
    }

    /**
     * Get the children of the given element
     * @param {any} element 
     * @returns {Promise<vscode.TreeItem[]>}
     */
    async getChildren(element) {
        if (element) {
            return [];
        }

        try {
            const changes = await this.gitService.getChanges();
            
            if (!changes || changes.length === 0) {
                return [new vscode.TreeItem('No changes detected', vscode.TreeItemCollapsibleState.None)];
            }

            return changes.map(change => {
                const { path, status } = change;
                
                // Create a tree item for each file
                const treeItem = new vscode.TreeItem(path, vscode.TreeItemCollapsibleState.None);
                
                // Set the context value to 'file' so we can use it in the when clause
                treeItem.contextValue = 'file';
                
                // Store the file path and status in the tree item
                treeItem.id = path;
                treeItem.tooltip = `${this.getStatusLabel(status)}: ${path}`;
                treeItem.command = {
                    command: 'openhands-changes-viewer.viewDiff',
                    title: 'View Diff',
                    arguments: [change]
                };
                
                // Set the icon based on the status
                treeItem.iconPath = this.getIconForStatus(status);
                
                return treeItem;
            });
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to get changes: ${error.message}`);
            return [new vscode.TreeItem(`Error: ${error.message}`, vscode.TreeItemCollapsibleState.None)];
        }
    }

    /**
     * Get a human-readable label for a git status
     * @param {string} status 
     * @returns {string}
     */
    getStatusLabel(status) {
        const statusMap = {
            'M': 'Modified',
            'A': 'Added',
            'D': 'Deleted',
            'R': 'Renamed',
            'U': 'Untracked'
        };
        
        return statusMap[status] || status;
    }

    /**
     * Get the icon for a git status
     * @param {string} status 
     * @returns {vscode.ThemeIcon}
     */
    getIconForStatus(status) {
        const iconMap = {
            'M': new vscode.ThemeIcon('edit'),
            'A': new vscode.ThemeIcon('add'),
            'D': new vscode.ThemeIcon('trash'),
            'R': new vscode.ThemeIcon('arrow-right'),
            'U': new vscode.ThemeIcon('question')
        };
        
        return iconMap[status] || new vscode.ThemeIcon('file');
    }
}

module.exports = { ChangesProvider };