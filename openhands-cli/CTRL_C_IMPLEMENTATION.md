# Ctrl+C Implementation for OpenHands CLI

## Overview

This implementation adds improved Ctrl+C handling to the OpenHands CLI where:
1. **First Ctrl+C**: Attempts graceful pause of the agent
2. **Second Ctrl+C** (within 3 seconds): Immediately kills the process

## Architecture

### Signal Handling (`signal_handler.py`)

**SignalHandler Class:**
- Tracks Ctrl+C presses with a 3-second timeout
- First press: calls graceful shutdown callback
- Second press: forces immediate exit with `os._exit(1)`

**ProcessSignalHandler Class:**
- Manages conversation runner processes
- Implements graceful shutdown by terminating the process
- Provides clean installation/uninstallation of signal handlers

### Process Management (`process_runner.py`)

**ProcessBasedConversationRunner Class:**
- Runs conversation in a separate process using `multiprocessing`
- Provides inter-process communication via queues
- Supports commands: process_message, get_status, toggle_confirmation_mode, resume
- Handles process lifecycle (start, stop, cleanup)

### Modified Components

**Pause Listener (`listeners/pause_listener.py`):**
- Removed Ctrl+C and Ctrl+D handling (now handled by signal handler)
- Only handles Ctrl+P for pause functionality

**Agent Chat (`agent_chat.py`):**
- Integrated ProcessSignalHandler for Ctrl+C management
- Updated to use ProcessBasedConversationRunner
- All commands (/new, /status, /confirm, /resume) work with process-based approach
- Proper cleanup in finally block

**Simple Main (`simple_main.py`):**
- Added basic SignalHandler installation for graceful shutdown

## Key Features

### Graceful Shutdown
- First Ctrl+C sends SIGTERM to conversation process
- Gives 2 seconds for graceful shutdown
- Shows appropriate user feedback

### Immediate Termination
- Second Ctrl+C within 3 seconds forces immediate exit
- Uses `os._exit(1)` to bypass Python cleanup
- Ensures agent stops immediately

### Process Communication
- Queue-based communication between main and conversation processes
- Status queries work across process boundaries
- Command handling preserved for all CLI features

### Error Handling
- Proper exception handling in both processes
- Cleanup of resources in finally blocks
- Fallback KeyboardInterrupt handlers

## Usage

The implementation is transparent to users:
- Press Ctrl+C once to pause the agent gracefully
- Press Ctrl+C again within 3 seconds to force immediate termination
- All existing CLI commands continue to work

## Testing

A test script `test_ctrl_c.py` is provided to verify the signal handling behavior:
```bash
uv run python test_ctrl_c.py
```

## Files Modified/Created

**New Files:**
- `openhands_cli/signal_handler.py` - Signal handling classes
- `openhands_cli/process_runner.py` - Process-based conversation runner
- `test_ctrl_c.py` - Test script for Ctrl+C behavior

**Modified Files:**
- `openhands_cli/listeners/pause_listener.py` - Removed Ctrl+C handling
- `openhands_cli/agent_chat.py` - Integrated new signal handling and process runner
- `openhands_cli/simple_main.py` - Added basic signal handler

## Dependencies

Uses standard Python libraries:
- `signal` - For signal handling
- `multiprocessing` - For separate process execution
- `queue` - For inter-process communication
- `threading` - For thread-safe signal counting
- `time` - For timeout management