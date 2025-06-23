# Terminal Reuse Problem Analysis

## Problem Statement

When launching `openhands --task "selected text"` from VS Code, we want to:
- **Reuse existing OpenHands terminal** if it exists AND is idle (no running process)
- **Create new terminal** if no OpenHands terminal exists OR existing terminal is busy

**Current Issue:** If an OpenHands terminal exists but has a running process (OH CLI or other app), sending new commands creates a mess by interfering with the running process.

## Technical Constraints

**VS Code API Limitations:**
- `vscode.Terminal` API doesn't expose process state information
- No direct way to check if a terminal has running processes
- Cannot query terminal for current prompt state
- Cannot reliably detect if terminal is "idle" vs "busy"

## Solution Approaches

### Approach 1: Interrupt-and-Reuse Strategy ⭐ **RECOMMENDED**

**Concept:** Always reuse the most recent OpenHands terminal, but safely interrupt any running process first.

**Implementation:**
```typescript
function findOrCreateOpenHandsTerminal(): vscode.Terminal {
  const openHandsTerminals = vscode.window.terminals.filter(
    terminal => terminal.name.startsWith('OpenHands')
  );
  
  if (openHandsTerminals.length > 0) {
    // Use most recent terminal
    const terminal = openHandsTerminals[openHandsTerminals.length - 1];
    
    // Safely interrupt any running process
    terminal.sendText('\u0003', false); // Send Ctrl+C
    
    // Brief pause to let interrupt take effect
    setTimeout(() => {
      terminal.sendText('clear', true); // Clear screen
    }, 100);
    
    return terminal;
  }
  
  // Create new terminal if none exist
  const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
  return vscode.window.createTerminal(`OpenHands ${timestamp}`);
}
```

**Pros:**
- Simple and reliable
- Always works regardless of terminal state
- User sees clean terminal after interrupt
- Preserves terminal history

**Cons:**
- Interrupts running processes (but this is often desired behavior)
- Brief delay due to interrupt sequence

### Approach 2: State Tracking Strategy

**Concept:** Track terminal state in extension memory and only reuse known-idle terminals.

**Implementation:**
```typescript
// Extension-level state tracking
const terminalStates = new Map<string, 'idle' | 'busy'>();

function startOpenHandsInTerminal(options: { task?: string; filePath?: string }): void {
  const idleTerminal = findIdleOpenHandsTerminal();
  
  if (idleTerminal) {
    // Mark as busy and use existing terminal
    terminalStates.set(idleTerminal.name, 'busy');
    sendCommandToTerminal(idleTerminal, buildCommand(options));
  } else {
    // Create new terminal
    const terminal = createNewOpenHandsTerminal();
    terminalStates.set(terminal.name, 'busy');
    sendCommandToTerminal(terminal, buildCommand(options));
  }
}

function findIdleOpenHandsTerminal(): vscode.Terminal | null {
  const openHandsTerminals = vscode.window.terminals.filter(
    terminal => terminal.name.startsWith('OpenHands')
  );
  
  return openHandsTerminals.find(terminal => 
    terminalStates.get(terminal.name) === 'idle'
  ) || null;
}
```

**Pros:**
- Never interrupts running processes
- Precise control over terminal usage
- Can maintain multiple idle terminals

**Cons:**
- Complex state management
- State can become out of sync with reality
- Requires tracking terminal lifecycle events
- User might manually run commands, breaking state tracking

### Approach 3: Probe-and-Detect Strategy

**Concept:** Send a probe command to test if terminal is responsive before reusing.

**Implementation:**
```typescript
async function findIdleOpenHandsTerminal(): Promise<vscode.Terminal | null> {
  const openHandsTerminals = vscode.window.terminals.filter(
    terminal => terminal.name.startsWith('OpenHands')
  );
  
  if (openHandsTerminals.length === 0) return null;
  
  const terminal = openHandsTerminals[openHandsTerminals.length - 1];
  
  // Send probe command
  terminal.sendText('echo "PROBE_RESPONSE"', true);
  
  // Wait and check if we can detect the response
  // (This is tricky with VS Code API - no direct way to read terminal output)
  
  return terminal; // Simplified - actual implementation would need output detection
}
```

**Pros:**
- Non-destructive testing
- Accurate idle detection

**Cons:**
- VS Code API doesn't provide terminal output reading
- Complex implementation
- Unreliable without output capture

### Approach 4: Always Create New Terminal

**Concept:** Always create a new terminal for each command to avoid conflicts.

**Implementation:**
```typescript
function startOpenHandsInTerminal(options: { task?: string; filePath?: string }): void {
  const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false });
  const terminal = vscode.window.createTerminal(`OpenHands ${timestamp}`);
  
  sendCommandToTerminal(terminal, buildCommand(options));
}
```

**Pros:**
- Simple and reliable
- No conflicts with running processes
- Each task gets clean environment

**Cons:**
- Terminal proliferation
- User ends up with many terminals
- Not what user requested

## Recommendation

**Use Approach 1: Interrupt-and-Reuse Strategy**

**Rationale:**
1. **Simplicity:** Easy to implement and understand
2. **Reliability:** Always works regardless of terminal state
3. **User Experience:** Provides predictable behavior
4. **Safety:** Ctrl+C is a standard way to interrupt processes
5. **Practicality:** Most users expect this behavior when launching new tasks

**Implementation Priority:**
1. Implement basic interrupt-and-reuse
2. Add user preference for "always create new terminal" vs "reuse terminal"
3. Consider adding state tracking as future enhancement

## Code Changes Required

**File:** `src/extension.ts`
**Function:** `startOpenHandsInTerminal`

**Current behavior:** Always creates new terminal
**New behavior:** Find existing OpenHands terminal, interrupt safely, then reuse

**Configuration option to add:**
```json
"openhands.terminal.reuseStrategy": {
  "type": "string",
  "enum": ["reuse", "always-new"],
  "default": "reuse",
  "description": "Whether to reuse existing OpenHands terminals or always create new ones"
}
```