const { exec } = require('child_process');
const os = require('os');

class ProcessMonitor {
    constructor() {
        this.platform = os.platform();
    }

    /**
     * Get detailed process information based on the platform
     * @param {Function} callback - Callback function to receive process data
     */
    getProcessInfo(callback) {
        if (this.platform === 'linux') {
            this.getLinuxProcessInfo(callback);
        } else if (this.platform === 'darwin') {
            this.getMacProcessInfo(callback);
        } else if (this.platform === 'win32') {
            this.getWindowsProcessInfo(callback);
        } else {
            callback(new Error(`Unsupported platform: ${this.platform}`), null);
        }
    }

    /**
     * Get process information on Linux
     * @param {Function} callback - Callback function to receive process data
     */
    getLinuxProcessInfo(callback) {
        // Get top processes by memory usage
        exec('ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%mem | head -n 11', (error, stdout) => {
            if (error) {
                callback(error, null);
                return;
            }

            // Parse the output
            const lines = stdout.trim().split('\n');
            const header = lines[0];
            const processes = lines.slice(1).map(line => {
                const parts = line.trim().split(/\s+/);
                const pid = parts[0];
                const ppid = parts[1];
                const memPercent = parseFloat(parts[parts.length - 2]);
                const cpuPercent = parseFloat(parts[parts.length - 1]);
                const cmd = parts.slice(2, parts.length - 2).join(' ');

                return {
                    pid,
                    ppid,
                    cmd,
                    memPercent,
                    cpuPercent
                };
            });

            callback(null, { header, processes });
        });
    }

    /**
     * Get process information on macOS
     * @param {Function} callback - Callback function to receive process data
     */
    getMacProcessInfo(callback) {
        // Similar to Linux but with slightly different ps command
        exec('ps -eo pid,ppid,command,%mem,%cpu -r | head -n 11', (error, stdout) => {
            if (error) {
                callback(error, null);
                return;
            }

            // Parse the output
            const lines = stdout.trim().split('\n');
            const header = lines[0];
            const processes = lines.slice(1).map(line => {
                const parts = line.trim().split(/\s+/);
                const pid = parts[0];
                const ppid = parts[1];
                const memPercent = parseFloat(parts[parts.length - 2]);
                const cpuPercent = parseFloat(parts[parts.length - 1]);
                const cmd = parts.slice(2, parts.length - 2).join(' ');

                return {
                    pid,
                    ppid,
                    cmd,
                    memPercent,
                    cpuPercent
                };
            });

            callback(null, { header, processes });
        });
    }

    /**
     * Get process information on Windows
     * @param {Function} callback - Callback function to receive process data
     */
    getWindowsProcessInfo(callback) {
        // Windows command to get process info
        exec('wmic process get ProcessId,ParentProcessId,CommandLine,WorkingSetSize /format:csv', (error, stdout) => {
            if (error) {
                callback(error, null);
                return;
            }

            // Parse the CSV output
            const lines = stdout.trim().split('\n');
            const header = "PID,PPID,Command,Memory (bytes)";

            // Skip empty lines and the header
            const dataLines = lines.filter(line => line.trim() !== '' && !line.includes('Node,'));

            const processes = dataLines.map(line => {
                const parts = line.split(',');
                if (parts.length < 4) return null;

                // Last part is the node name, then ProcessId, ParentProcessId, CommandLine, WorkingSetSize
                const pid = parts[parts.length - 4];
                const ppid = parts[parts.length - 3];
                const cmd = parts[parts.length - 2];
                const memBytes = parseInt(parts[parts.length - 1], 10);
                const memPercent = (memBytes / os.totalmem() * 100).toFixed(1);

                return {
                    pid,
                    ppid,
                    cmd,
                    memPercent,
                    memBytes
                };
            }).filter(Boolean)
              .sort((a, b) => b.memBytes - a.memBytes)
              .slice(0, 10);

            callback(null, { header, processes });
        });
    }
}

module.exports = ProcessMonitor;
