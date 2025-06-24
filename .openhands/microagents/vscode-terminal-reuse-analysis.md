# VSCode Extension Terminal Reuse - Development Analysis

This document contains the detailed technical analysis and decision-making process for implementing safe terminal reuse in the OpenHands VSCode extension. This is development-time documentation that explains the various approaches considered and why the current implementation was chosen.

## Problem Statement

When launching `openhands --task "selected text"` from VS Code, we want to:
- **Reuse existing OpenHands terminal** if it exists AND is idle (no running process)
- **Create new terminal** if no OpenHands terminal exists OR existing terminal is busy

**Current Issue:** If an OpenHands terminal exists but has a running process (OH CLI or other app), sending new commands creates a mess by interfering with the running process.

## Technical Capabilities

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

## Solution Approaches Considered

### Approach 1: Shell Integration with Intelligent Probing (ABANDONED)

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
```

**Why Abandoned:**
1. **Probing commands interrupted running processes** - Even simple `echo` commands could interfere with CLIs
2. **Shell Integration executeCommand() was too intrusive** - It would interrupt running processes to execute probe commands
3. **User experience was poor** - Users reported that their running CLIs were being stopped

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
- **Actually interrupts processes** - The main reason for abandonment

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

## Final Implementation: Safe State Tracking

**Primary: Safe State Tracking (Modified Approach 4)**
**Fallback: Always Create New Terminal (Approach 3)**

### Current Implementation

The extension now uses a **Safe State Tracking** approach that eliminates the risk of interrupting running processes:

**Key Principles:**
1. **Never probe busy terminals** - No commands are sent to terminals that might be running processes
2. **Track only our own commands** - Only reuse terminals where we know our OpenHands commands have completed
3. **Safe fallback** - Create new terminals when in doubt

**Implementation Details:**
```typescript
// Track terminals that we know are idle (completed our commands)
const idleTerminals = new Set<string>();

function findOrCreateOpenHandsTerminal(): vscode.Terminal {
  const openHandsTerminals = vscode.window.terminals.filter(
    terminal => terminal.name.startsWith('OpenHands')
  );

  if (openHandsTerminals.length > 0) {
    const terminal = openHandsTerminals[openHandsTerminals.length - 1];

    // Only reuse terminals that we know are idle (safe to reuse)
    if (isKnownIdleTerminal(terminal)) {
      return terminal;
    }

    // If we don't know the terminal is idle, create new one
    return createNewOpenHandsTerminal();
  }

  return createNewOpenHandsTerminal();
}
```

**State Tracking:**
- Terminals are marked as busy when we start commands
- Terminals are marked as idle when our commands complete (using Shell Integration events)
- Terminals without Shell Integration are never marked as idle (safer)
- Terminal state is cleaned up when terminals are closed

**Benefits:**
- **Zero interruption risk** - Never sends commands to potentially busy terminals
- **Efficient reuse** - Reuses terminals that have completed OpenHands commands
- **Shell Integration aware** - Uses modern VS Code APIs when available
- **Graceful degradation** - Works safely even without Shell Integration

## Code Changes Implemented

**File:** `src/extension.ts`
**Functions implemented:**
- `markTerminalAsIdle()` / `markTerminalAsBusy()` - Track terminal states safely
- `isKnownIdleTerminal()` - Check if terminal is safe to reuse
- `findOrCreateOpenHandsTerminal()` - Safe terminal selection logic
- `executeOpenHandsCommand()` - Command execution with state tracking

**Previous behavior:** Always creates new terminal with timestamp
**New behavior:**
1. Check for existing OpenHands terminals
2. If found and known to be idle: reuse terminal
3. If found but state unknown: create new terminal (safe fallback)
4. Track command completion using Shell Integration events
5. Clean up state when terminals are closed

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

## Implementation Rationale

1. **Safety First:** Never risk interrupting user processes
2. **Simple State Tracking:** Only track terminals where we executed commands
3. **Shell Integration for Monitoring:** Use Shell Integration only to monitor our own command completion
4. **Conservative Reuse:** Only reuse terminals we know are safe
5. **Predictable Behavior:** Always create new terminals when in doubt

## References for Implementation

**VSCode API Documentation:**
- [Terminal Shell Integration](https://code.visualstudio.com/docs/terminal/shell-integration)
- [VSCode Extension API](https://code.visualstudio.com/api/references/vscode-api)
- [Terminal API Reference](https://code.visualstudio.com/api/references/vscode-api#Terminal)

**Shell Integration Examples:**
- [VSCode Source Examples](https://github.com/microsoft/vscode/blob/main/src/vscode-dts/vscode.d.ts)
- Shell Integration requires: bash, zsh, PowerShell Core, or fish shell
- Graceful fallback needed for Command Prompt and other shells

## Development Notes

This analysis was created during the development of the OpenHands VSCode extension to document the decision-making process for terminal reuse functionality. The final implementation prioritizes user safety and experience over complex optimization.

Key lessons learned:
1. Probing terminals is inherently risky and should be avoided
2. Shell Integration is powerful but must be used carefully
3. Conservative approaches often provide better user experience
4. State tracking should be simple and fail-safe