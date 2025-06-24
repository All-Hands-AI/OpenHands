# VSCode Integration with OpenHands

This document outlines the three main approaches for integrating VSCode with OpenHands, each serving different use cases and levels of integration.

## Overview

There are three distinct integration approaches being developed:

1. **VSCode Integration Extension** - Simple menu integration
2. **VSCode Runtime** - Execution environment integration
3. **OpenHands Tab** - Full UI integration

## 1. VSCode Integration Extension (vscode-integration)

**Purpose**: Provides a simple way to launch OpenHands from within VSCode.

**Features**:
- Auto-installs as a VSCode extension
- Adds commands to VSCode's command palette and menus
- Allows users to start OpenHands sessions directly from VSCode
- Minimal integration - primarily a launcher

**Implementation**:
- VSCode extension (TypeScript/JavaScript)
- Located in `/openhands/integrations/vscode/`
- Focuses on VSCode extension API for menu integration

**Use Case**: Users who want to quickly start OpenHands while working in VSCode without leaving their editor environment.

## 2. VSCode Runtime (vscode-runtime)

**Purpose**: Executes OpenHands actions directly within the VSCode environment using VSCode APIs.

**Features**:
- Implements the OpenHands Runtime interface
- Actions are executed in TypeScript using VSCode API
- File operations, terminal commands, etc. run through VSCode's built-in capabilities
- Provides a sandboxed execution environment within VSCode

**Implementation**:
- Python Runtime class: `/openhands/runtime/vscode/vscode_runtime.py`
- TypeScript action handlers using VSCode API
- Communication bridge between Python OpenHands core and TypeScript execution

**Use Case**: Users who want OpenHands actions to be executed directly in their VSCode workspace, leveraging VSCode's file system access, terminal, and other built-in features.

**Current Status**: Implementation exists but has issues with assumptions about Socket.IO connections and other infrastructure that may not be properly set up.

## 3. OpenHands Tab (openhands-tab)

**Purpose**: Provides a complete OpenHands user interface as a tab within VSCode.

**Features**:
- Full OpenHands UI embedded in VSCode
- Users can send prompts, view agent actions and observations
- Complete conversation history and interaction capabilities
- Seamless integration with VSCode workspace

**Implementation**:
- VSCode webview panel hosting OpenHands frontend
- Frontend components adapted for VSCode environment
- Located in `/frontend/src/routes/vscode-tab.tsx`

**Use Case**: Users who want the full OpenHands experience without leaving VSCode, with complete access to all OpenHands features in a native VSCode interface.

## Integration Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ VSCode          │    │ OpenHands Core   │    │ Execution       │
│ Integration     │    │ (Python)         │    │ Environment     │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ 1. Menu Commands│───▶│ Agent Controller │    │ Local/Docker/   │
│ 2. Runtime API  │◀──▶│ Runtime Interface│◀──▶│ Remote/VSCode   │
│ 3. UI Tab       │    │ Event Stream     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Current Focus: VSCode Runtime

The current task focuses on **approach #2 (VSCode Runtime)**. This involves:

- Implementing a proper Runtime class that executes actions via VSCode API
- Setting up communication between Python OpenHands core and TypeScript execution
- Handling file operations, terminal commands, and other actions through VSCode's capabilities
- Ensuring proper error handling and observation reporting

The existing implementation in `vscode_runtime.py` needs review and fixes for assumptions about infrastructure that may not exist.
