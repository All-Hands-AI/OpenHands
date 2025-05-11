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
            // Use -z to handle filenames with special characters
            const { stdout } = await execAsync('git status --porcelain -z', { cwd: this.workspaceRoot });

            if (!stdout) {
                return [];
            }

            // Parse the output of git status with null-terminated lines
            const changes = [];
            const entries = stdout.split('\0');

            for (let i = 0; i < entries.length - 1; i++) {
                const entry = entries[i];
                if (entry.length >= 2) {
                    const status = entry.substring(0, 2).trim();
                    const path = entry.substring(3);

                    // Skip empty paths
                    if (!path) continue;

                    // Map the git status to our status codes
                    let mappedStatus = 'M'; // Default to modified

                    if (status.includes('A') || status.includes('?')) {
                        mappedStatus = 'A'; // Added or untracked
                    } else if (status.includes('D')) {
                        mappedStatus = 'D'; // Deleted
                    } else if (status.includes('R')) {
                        mappedStatus = 'R'; // Renamed
                    }

                    changes.push({ path, status: mappedStatus });
                }
            }

            return changes;
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
            // Properly escape the file path for shell commands
            const escapedPath = filePath.replace(/'/g, "'\\''");

            // Check if the file exists in the index
            const { stdout: fileStatus } = await execAsync(`git status --porcelain -- '${escapedPath}'`, {
                cwd: this.workspaceRoot
            });

            const status = fileStatus.substring(0, 2).trim();
            let original = '';
            let modified = '';

            if (status.includes('?') || status.includes('A')) {
                // New file - get the current content
                try {
                    const { stdout: currentContent } = await execAsync(`cat '${escapedPath}'`, {
                        cwd: this.workspaceRoot
                    });
                    original = '';
                    modified = currentContent;
                } catch (error) {
                    console.warn(`Warning: Could not read new file: ${error.message}`);
                    original = '';
                    modified = '';
                }
            } else if (status.includes('D')) {
                // Deleted file - get the content from the index
                try {
                    // Use a more reliable way to get the file from git
                    const { stdout: indexContent } = await execAsync(`git show HEAD:'${escapedPath}'`, {
                        cwd: this.workspaceRoot
                    });
                    original = indexContent;
                    modified = '';
                } catch (error) {
                    console.warn(`Warning: Could not get deleted file content: ${error.message}`);
                    original = '';
                    modified = '';
                }
            } else {
                // Modified file - get both versions
                try {
                    // Get the content from the index
                    const { stdout: indexContent } = await execAsync(`git show HEAD:'${escapedPath}'`, {
                        cwd: this.workspaceRoot
                    });
                    original = indexContent;
                } catch (error) {
                    // File might not exist in the index yet
                    console.warn(`Warning: Could not get original file content: ${error.message}`);
                    original = '';
                }

                try {
                    // Get the current content
                    const { stdout: currentContent } = await execAsync(`cat '${escapedPath}'`, {
                        cwd: this.workspaceRoot
                    });
                    modified = currentContent;
                } catch (error) {
                    // File might not exist in the workspace
                    console.warn(`Warning: Could not get modified file content: ${error.message}`);
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
