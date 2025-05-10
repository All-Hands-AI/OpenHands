const os = require('os');
const vscode = require('vscode');
const ProcessMonitor = require('./process_monitor');

class MemoryMonitor {
    constructor() {
        this.isMonitoring = false;
        this.intervalId = null;
        this.statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.statusBarItem.command = 'openhands-memory-monitor.showMemoryDetails';
        this.processMonitor = new ProcessMonitor();
        this.memoryHistory = [];
        this.maxHistoryLength = 60; // Keep 5 minutes of data with 5-second intervals
        this.context = null; // Will be set in activate
    }

    start(interval = 5000) {
        if (this.isMonitoring) {
            return;
        }

        this.isMonitoring = true;
        this.statusBarItem.show();

        // Initial update
        this.updateMemoryInfo();

        // Set interval for updates
        this.intervalId = setInterval(() => {
            this.updateMemoryInfo();
        }, interval);

        vscode.window.showInformationMessage('Memory monitoring started');
    }

    stop() {
        if (!this.isMonitoring) {
            return;
        }

        this.isMonitoring = false;
        clearInterval(this.intervalId);
        this.statusBarItem.hide();

        vscode.window.showInformationMessage('Memory monitoring stopped');
    }

    updateMemoryInfo() {
        const totalMem = os.totalmem();
        const freeMem = os.freemem();
        const usedMem = totalMem - freeMem;

        // Calculate memory usage percentage
        const memUsagePercent = Math.round((usedMem / totalMem) * 100);

        // Format memory values to MB
        const usedMemMB = Math.round(usedMem / (1024 * 1024));
        const totalMemMB = Math.round(totalMem / (1024 * 1024));

        // Update status bar
        this.statusBarItem.text = `$(pulse) Mem: ${memUsagePercent}%`;
        this.statusBarItem.tooltip = `Memory Usage: ${usedMemMB}MB / ${totalMemMB}MB`;

        // Store memory data in history
        this.memoryHistory.push({
            timestamp: new Date(),
            usedMemMB,
            totalMemMB,
            memUsagePercent,
            processMemory: process.memoryUsage()
        });

        // Limit history length
        if (this.memoryHistory.length > this.maxHistoryLength) {
            this.memoryHistory.shift();
        }
    }

    showDetails() {
        // Create and show a webview panel with detailed memory information
        const panel = vscode.window.createWebviewPanel(
            'memoryMonitor',
            'Memory Monitor',
            vscode.ViewColumn.One,
            {
                enableScripts: true
            }
        );

        // Set up message handler for real-time updates
        panel.webview.onDidReceiveMessage(
            message => {
                if (message.command === 'requestUpdate') {
                    this.updateWebviewContent(panel);
                }
            },
            undefined,
            this.context ? this.context.subscriptions : []
        );

        // Initial update
        this.updateWebviewContent(panel);

        // Handle panel disposal
        panel.onDidDispose(() => {
            // Clean up any resources if needed
        }, null, this.context ? this.context.subscriptions : []);
    }

    updateWebviewContent(panel) {
        // Get system memory info
        const totalMem = os.totalmem();
        const freeMem = os.freemem();
        const usedMem = totalMem - freeMem;

        // Format memory values
        const usedMemMB = Math.round(usedMem / (1024 * 1024));
        const freeMemMB = Math.round(freeMem / (1024 * 1024));
        const totalMemMB = Math.round(totalMem / (1024 * 1024));

        // Get process memory usage
        const processMemory = process.memoryUsage();
        const rss = Math.round(processMemory.rss / (1024 * 1024));
        const heapTotal = Math.round(processMemory.heapTotal / (1024 * 1024));
        const heapUsed = Math.round(processMemory.heapUsed / (1024 * 1024));

        // Get process information
        this.processMonitor.getProcessInfo((error, processInfo) => {
            if (error) {
                console.error('Error getting process info:', error);
                return;
            }

            // Create HTML content for the webview
            const htmlContent = this.generateHtmlReport(
                usedMemMB, freeMemMB, totalMemMB,
                rss, heapTotal, heapUsed,
                processInfo
            );

            // Set the webview's HTML content
            panel.webview.html = htmlContent;
        });
    }

    generateHtmlReport(usedMemMB, freeMemMB, totalMemMB, rss, heapTotal, heapUsed, processInfo) {
        // Create memory usage history data for chart
        const memoryLabels = this.memoryHistory.map((entry, index) => index);
        const memoryData = this.memoryHistory.map(entry => entry.memUsagePercent);
        const heapData = this.memoryHistory.map(entry =>
            Math.round(entry.processMemory.heapUsed / (1024 * 1024))
        );

        // Format process info table
        let processTable = '';
        if (processInfo && processInfo.processes) {
            processTable = `
                <h3>Top Processes by Memory Usage</h3>
                <table>
                    <tr>
                        <th>PID</th>
                        <th>Memory %</th>
                        <th>CPU %</th>
                        <th>Command</th>
                    </tr>
                    ${processInfo.processes.map(proc => `
                        <tr>
                            <td>${proc.pid}</td>
                            <td>${proc.memPercent}%</td>
                            <td>${proc.cpuPercent || 'N/A'}</td>
                            <td>${proc.cmd}</td>
                        </tr>
                    `).join('')}
                </table>
            `;
        }

        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Memory Monitor</title>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                        padding: 20px;
                        color: var(--vscode-foreground);
                        background-color: var(--vscode-editor-background);
                    }
                    .memory-card {
                        background-color: var(--vscode-editor-background);
                        border: 1px solid var(--vscode-panel-border);
                        border-radius: 5px;
                        padding: 15px;
                        margin-bottom: 20px;
                    }
                    .memory-info {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 20px;
                    }
                    .memory-stat {
                        flex: 1;
                        min-width: 200px;
                    }
                    .memory-value {
                        font-size: 24px;
                        font-weight: bold;
                        margin: 10px 0;
                    }
                    .memory-label {
                        font-size: 14px;
                        color: var(--vscode-descriptionForeground);
                    }
                    .chart-container {
                        height: 300px;
                        margin: 20px 0;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }
                    th, td {
                        text-align: left;
                        padding: 8px;
                        border-bottom: 1px solid var(--vscode-panel-border);
                    }
                    th {
                        background-color: var(--vscode-editor-background);
                        font-weight: bold;
                    }
                </style>
            </head>
            <body>
                <h1>Memory Monitor</h1>

                <div class="memory-card">
                    <h2>System Memory</h2>
                    <div class="memory-info">
                        <div class="memory-stat">
                            <div class="memory-label">Used Memory</div>
                            <div class="memory-value">${usedMemMB} MB</div>
                        </div>
                        <div class="memory-stat">
                            <div class="memory-label">Free Memory</div>
                            <div class="memory-value">${freeMemMB} MB</div>
                        </div>
                        <div class="memory-stat">
                            <div class="memory-label">Total Memory</div>
                            <div class="memory-value">${totalMemMB} MB</div>
                        </div>
                        <div class="memory-stat">
                            <div class="memory-label">Usage</div>
                            <div class="memory-value">${Math.round(usedMemMB / totalMemMB * 100)}%</div>
                        </div>
                    </div>
                </div>

                <div class="memory-card">
                    <h2>Process Memory (VSCode Extension Host)</h2>
                    <div class="memory-info">
                        <div class="memory-stat">
                            <div class="memory-label">RSS</div>
                            <div class="memory-value">${rss} MB</div>
                        </div>
                        <div class="memory-stat">
                            <div class="memory-label">Heap Used</div>
                            <div class="memory-value">${heapUsed} MB</div>
                        </div>
                        <div class="memory-stat">
                            <div class="memory-label">Heap Total</div>
                            <div class="memory-value">${heapTotal} MB</div>
                        </div>
                    </div>
                </div>

                <div class="memory-card">
                    <h2>Memory Usage History</h2>
                    <div class="chart-container">
                        <canvas id="memoryChart"></canvas>
                    </div>
                </div>

                <div class="memory-card">
                    ${processTable}
                </div>

                <script>
                    // Create memory usage chart
                    const ctx = document.getElementById('memoryChart').getContext('2d');
                    const memoryChart = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: ${JSON.stringify(memoryLabels)},
                            datasets: [
                                {
                                    label: 'System Memory Usage (%)',
                                    data: ${JSON.stringify(memoryData)},
                                    borderColor: 'rgba(75, 192, 192, 1)',
                                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                    tension: 0.4
                                },
                                {
                                    label: 'Process Heap Usage (MB)',
                                    data: ${JSON.stringify(heapData)},
                                    borderColor: 'rgba(255, 99, 132, 1)',
                                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                                    tension: 0.4
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }
                    });

                    // Set up real-time updates
                    const vscode = acquireVsCodeApi();

                    // Request updates every 5 seconds
                    setInterval(() => {
                        vscode.postMessage({
                            command: 'requestUpdate'
                        });
                    }, 5000);
                </script>
            </body>
            </html>
        `;
    }
}

module.exports = MemoryMonitor;
