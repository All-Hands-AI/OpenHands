const vscode = require('vscode');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

/**
 * Service for interacting with Git
 */
class GitService {
    constructor() {
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    }

    /**
     * Get the list of changed files
     * @returns {Promise<Array<{path: string, status: string}>>}
     */
    async getChanges() {
        if (!this.workspaceRoot) {
            throw new Error('No workspace folder is open');
        }

        try {
            // Run git status to get the list of changed files
            const { stdout } = await execAsync('git status --porcelain', { cwd: this.workspaceRoot });
            
            if (!stdout.trim()) {
                return [];
            }
            
            // Parse the output of git status
            return stdout.trim().split('\n').map(line => {
                const status = line.substring(0, 2).trim();
                const path = line.substring(3).trim();
                
                // Map the git status to our status codes
                let mappedStatus = 'M'; // Default to modified
                
                if (status.includes('A') || status.includes('?')) {
                    mappedStatus = 'A'; // Added or untracked
                } else if (status.includes('D')) {
                    mappedStatus = 'D'; // Deleted
                } else if (status.includes('R')) {
                    mappedStatus = 'R'; // Renamed
                }
                
                return { path, status: mappedStatus };
            });
        } catch (error) {
            console.error('Error getting git changes:', error);
            throw new Error(`Failed to get git changes: ${error.message}`);
        }
    }

    /**
     * Get the diff for a file
     * @param {string} filePath 
     * @returns {Promise<{original: string, modified: string}>}
     */
    async getDiff(filePath) {
        if (!this.workspaceRoot) {
            throw new Error('No workspace folder is open');
        }

        try {
            // Check if the file exists in the index
            const { stdout: fileStatus } = await execAsync(`git status --porcelain -- "${filePath}"`, { 
                cwd: this.workspaceRoot 
            });
            
            const status = fileStatus.substring(0, 2).trim();
            let original = '';
            let modified = '';
            
            if (status.includes('?') || status.includes('A')) {
                // New file - get the current content
                const { stdout: currentContent } = await execAsync(`cat "${filePath}"`, { 
                    cwd: this.workspaceRoot 
                });
                original = '';
                modified = currentContent;
            } else if (status.includes('D')) {
                // Deleted file - get the content from the index
                const { stdout: indexContent } = await execAsync(`git show HEAD:"${filePath}"`, { 
                    cwd: this.workspaceRoot 
                });
                original = indexContent;
                modified = '';
            } else {
                // Modified file - get both versions
                try {
                    // Get the content from the index
                    const { stdout: indexContent } = await execAsync(`git show HEAD:"${filePath}"`, { 
                        cwd: this.workspaceRoot 
                    });
                    original = indexContent;
                } catch (error) {
                    // File might not exist in the index yet
                    original = '';
                }
                
                try {
                    // Get the current content
                    const { stdout: currentContent } = await execAsync(`cat "${filePath}"`, { 
                        cwd: this.workspaceRoot 
                    });
                    modified = currentContent;
                } catch (error) {
                    // File might not exist in the workspace
                    modified = '';
                }
            }
            
            return { original, modified };
        } catch (error) {
            console.error('Error getting diff:', error);
            throw new Error(`Failed to get diff: ${error.message}`);
        }
    }
}

module.exports = { GitService };