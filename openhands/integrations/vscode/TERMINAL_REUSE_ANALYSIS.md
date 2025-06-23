# Terminal Reuse Problem Analysis

## Problem Statement

When launching `openhands --task "selected text"` from VS Code, we want to:
- **Reuse existing OpenHands terminal** if it exists AND is idle (no running process)
- **Create new terminal** if no OpenHands terminal exists OR existing terminal is busy

**Current Issue:** If an OpenHands terminal exists but has a running process (OH CLI or other app), sending new commands creates a mess by interfering with the running process.

## Technical Capabilities (Updated 2024/2025)

**VSCode Shell Integration API** provides powerful new capabilities:
- `terminal.shellIntegration.executeCommand()` - Execute commands with full control
- `execution.read()` - Read terminal output as AsyncIterable<string>
- `execution.exitCode` - Get command exit codes
- `window.onDidEndTerminalShellExecution` - Monitor command completion
- **Safe interruption** - API automatically sends ^C to interrupt running commands

**API Availability:**
- Shell Integration requires compatible shells (bash, zsh, PowerShell, fish)
- Not available on Command Prompt (cmd.exe)
- May not activate if user's shell setup conflicts with integration
- Graceful fallback to traditional `sendText()` when unavailable

**References:**
- [VSCode API Documentation](https://code.visualstudio.com/api/references/vscode-api)
- [Shell Integration Guide](https://code.visualstudio.com/docs/terminal/shell-integration)
- [VSCode Source: vscode.d.ts](https://github.com/microsoft/vscode/blob/main/src/vscode-dts/vscode.d.ts)

## Solution Approaches

### Approach 1: Shell Integration with Intelligent Probing ⭐ **NEW RECOMMENDED**

**Concept:** Use VSCode's Shell Integration API to intelligently detect terminal state and safely manage commands.

**Implementation:**
```typescript
async function findOrCreateOpenHandsTerminal(): Promise<vscode.Terminal> {
  const openHandsTerminals = vscode.window.terminals.filter(
    terminal => terminal.name.startsWith('OpenHands')
  );

  if (openHandsTerminals.length > 0) {
    const terminal = openHandsTerminals[openHandsTerminals.length - 1];

    if (terminal.shellIntegration) {
      // Use intelligent probing with Shell Integration
      const isIdle = await probeTerminalStatus(terminal);
      if (isIdle) {
        return terminal; // Safe to reuse
      }
      // If busy, Shell Integration will safely interrupt when we execute new command
      return terminal;
    }

    // Fallback: create new terminal to avoid conflicts
    return createNewOpenHandsTerminal();
  }

  return createNewOpenHandsTerminal();
}

async function probeTerminalStatus(terminal: vscode.Terminal): Promise<boolean> {
  if (!terminal.shellIntegration) return false;

  try {
    const probeId = Date.now();
    const execution = terminal.shellIntegration.executeCommand(
      `echo "OPENHANDS_PROBE_${probeId}"`
    );

    // Read output to verify response
    const stream = execution.read();
    let output = '';
    const timeout = new Promise<boolean>((_, reject) =>
      setTimeout(() => reject(new Error('Probe timeout')), 2000)
    );

    const readOutput = async (): Promise<boolean> => {
      for await (const data of stream) {
        output += data;
        if (output.includes(`OPENHANDS_PROBE_${probeId}`)) {
          const exitCode = await execution.exitCode;
          return exitCode === 0;
        }
      }
      return false;
    };

    return await Promise.race([readOutput(), timeout]);
  } catch (error) {
    return false; // Assume busy if probe fails
  }
}

async function executeOpenHandsCommand(terminal: vscode.Terminal, command: string): Promise<void> {
  if (terminal.shellIntegration) {
    // Use Shell Integration for better control
    const execution = terminal.shellIntegration.executeCommand(command);

    // Monitor execution completion
    vscode.window.onDidEndTerminalShellExecution(event => {
      if (event.execution === execution) {
        if (event.exitCode === 0) {
          console.log('OpenHands command completed successfully');
        } else if (event.exitCode !== undefined) {
          console.log(`OpenHands command exited with code ${event.exitCode}`);
        }
      }
    });
  } else {
    // Fallback to traditional sendText
    terminal.sendText(command, true);
  }
}
```

**Pros:**
- **Intelligent detection** - Can actually determine if terminal is idle
- **Safe interruption** - API handles ^C automatically when needed
- **Output monitoring** - Can read command output and exit codes
- **Graceful fallback** - Works even when Shell Integration unavailable
- **Non-destructive probing** - Harmless echo command for testing

**Cons:**
- **Shell dependency** - Requires compatible shell (bash, zsh, PowerShell, fish)
- **Complexity** - More complex than simple approaches
- **Timing** - Probe adds small delay for detection

### Approach 2: Interrupt-and-Reuse Strategy (Fallback)

**Concept:** When Shell Integration unavailable, safely interrupt and reuse terminal.

**Implementation:**
```typescript
function interruptAndReuseTerminal(terminal: vscode.Terminal): vscode.Terminal {
  // Send Ctrl+C to interrupt any running process
  terminal.sendText('\u0003', false);

  // Brief pause to let interrupt take effect
  setTimeout(() => {
    terminal.sendText('clear', true); // Clear screen for clean start
  }, 100);

  return terminal;
}
```

**Pros:**
- Simple and reliable fallback
- Always works regardless of shell type
- User sees clean terminal after interrupt

**Cons:**
- Always interrupts, even if terminal was idle
- Brief delay due to interrupt sequence

### Approach 3: Always Create New Terminal (Current Fallback)

**Concept:** Always create a new terminal for each command to avoid conflicts entirely.

**Implementation:**
```typescript
function createNewOpenHandsTerminal(): vscode.Terminal {
  const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
  return vscode.window.createTerminal(`OpenHands ${timestamp}`);
}

function startOpenHandsInTerminal(options: { task?: string; filePath?: string }): void {
  const terminal = createNewOpenHandsTerminal();
  sendCommandToTerminal(terminal, buildCommand(options));
}
```

**Pros:**
- **Simple and reliable** - No complex logic needed
- **No conflicts** - Never interferes with running processes
- **Clean environment** - Each task gets fresh terminal
- **Predictable** - Always works the same way

**Cons:**
- **Terminal proliferation** - User accumulates many terminals
- **Resource usage** - More terminals consume more memory
- **User experience** - Not ideal for frequent usage

### Approach 4: State Tracking Strategy (Complex Alternative)

**Concept:** Track terminal state in extension memory, but now enhanced with Shell Integration.

**Implementation:**
```typescript
// Enhanced state tracking with Shell Integration
const terminalStates = new Map<string, {
  status: 'idle' | 'busy' | 'unknown',
  lastActivity: number,
  hasShellIntegration: boolean
}>();

function trackTerminalExecution(terminal: vscode.Terminal, execution: vscode.TerminalShellExecution): void {
  terminalStates.set(terminal.name, {
    status: 'busy',
    lastActivity: Date.now(),
    hasShellIntegration: true
  });

  // Listen for completion
  vscode.window.onDidEndTerminalShellExecution(event => {
    if (event.execution === execution) {
      terminalStates.set(terminal.name, {
        status: 'idle',
        lastActivity: Date.now(),
        hasShellIntegration: true
      });
    }
  });
}
```

**Pros:**
- **Precise tracking** - Knows exact terminal states
- **Shell Integration aware** - Leverages modern API capabilities
- **Multiple terminals** - Can manage several idle terminals

**Cons:**
- **Complex implementation** - Requires extensive state management
- **Sync issues** - State can drift from reality
- **Manual interference** - User commands break tracking
- **Over-engineering** - More complex than needed for most use cases

## Recommendation

**Primary: Shell Integration with Intelligent Probing (Approach 1)**
**Fallback: Always Create New Terminal (Approach 3)**

### Implementation Strategy

**Phase 1: Smart Detection with Graceful Fallback**
```typescript
async function findOrCreateOpenHandsTerminal(): Promise<vscode.Terminal> {
  const openHandsTerminals = vscode.window.terminals.filter(
    terminal => terminal.name.startsWith('OpenHands')
  );

  if (openHandsTerminals.length > 0) {
    const terminal = openHandsTerminals[openHandsTerminals.length - 1];

    if (terminal.shellIntegration) {
      // Try intelligent probing
      const isIdle = await probeTerminalStatus(terminal);
      if (isIdle) {
        return terminal; // Safe to reuse
      }
      // If busy, Shell Integration will handle interruption safely
      return terminal;
    }
  }

  // Fallback: create new terminal (no user nagging)
  return createNewOpenHandsTerminal();
}
```

### Rationale

1. **Modern API Usage:** Leverages VSCode's latest Shell Integration capabilities
2. **Intelligent Detection:** Actually determines if terminal is idle vs busy
3. **Safe Operation:** API handles interruption automatically when needed
4. **Graceful Degradation:** Falls back to new terminal creation when Shell Integration unavailable
5. **No User Interruption:** Avoids nagging users with choices
6. **Predictable Behavior:** Consistent experience across different shell environments

### Implementation Priority

**Phase 1: Basic Shell Integration Support**
- Implement intelligent probing for compatible shells
- Fallback to new terminal creation for incompatible environments
- Add Shell Integration detection and usage

**Phase 2: Enhanced Monitoring**
- Add execution monitoring with `onDidEndTerminalShellExecution`
- Implement output reading for better command feedback
- Add error handling for failed executions

**Phase 3: Configuration Options (Optional)**
- Add user preference for terminal reuse behavior
- Implement terminal cleanup/management features
- Add debugging/logging for Shell Integration status

## Code Changes Required

**File:** `src/extension.ts`
**Functions to modify:**
- `startOpenHandsInTerminal()` - Add Shell Integration detection
- Add `probeTerminalStatus()` - Implement intelligent probing
- Add `executeOpenHandsCommand()` - Use Shell Integration when available

**Current behavior:** Always creates new terminal with timestamp
**New behavior:**
1. Check for existing OpenHands terminals
2. If found and has Shell Integration: probe for idle status
3. If idle or Shell Integration handles interruption: reuse terminal
4. Otherwise: create new terminal with timestamp

**Configuration options (future):**
```json
"openhands.terminal.reuseStrategy": {
  "type": "string",
  "enum": ["smart", "always-new"],
  "default": "smart",
  "description": "Terminal reuse strategy: smart detection or always create new"
},
"openhands.terminal.maxTerminals": {
  "type": "number",
  "default": 5,
  "description": "Maximum number of OpenHands terminals to keep open"
}
```

## References for Implementation

**VSCode API Documentation:**
- [Terminal Shell Integration](https://code.visualstudio.com/docs/terminal/shell-integration)
- [VSCode Extension API](https://code.visualstudio.com/api/references/vscode-api)
- [Terminal API Reference](https://code.visualstudio.com/api/references/vscode-api#Terminal)

**Shell Integration Examples:**
- [VSCode Source Examples](https://github.com/microsoft/vscode/blob/main/src/vscode-dts/vscode.d.ts)
- Shell Integration requires: bash, zsh, PowerShell Core, or fish shell
- Graceful fallback needed for Command Prompt and other shells
