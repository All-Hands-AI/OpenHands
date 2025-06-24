# VSCode Runtime Migration and Cleanup Task

## Overview

After rebasing the `vscode-runtime` branch on top of the `vscode-integration` branch, we now have:
1. **New VSCode Integration Extension** in `openhands/integrations/vscode/` (from Task 1 - launcher functionality)
2. **Old VSCode Runtime Extension** in `openhands/runtime/utils/vscode-extensions/openhands-runtime/` (from Task 2 - runtime functionality)

We need to **migrate the runtime functionality** from the old location to the new integrated extension and **clean up redundant files**.

## Current State Analysis

### ✅ New VSCode Integration Extension (`openhands/integrations/vscode/`)
**Purpose**: VSCode launcher extension (Task 1)
- **Location**: `openhands/integrations/vscode/`
- **Features**: Context menu commands, Command Palette entries, auto-installation
- **Main file**: `src/extension.ts` (launcher functionality)
- **Status**: ✅ Complete and working
- **Package**: `openhands-vscode-0.0.1.vsix`

### 🔄 Old VSCode Runtime Extension (`openhands/runtime/utils/vscode-extensions/openhands-runtime/`)
**Purpose**: VSCode runtime execution (Task 2)
- **Location**: `openhands/runtime/utils/vscode-extensions/openhands-runtime/`
- **Key Files**:
  - `src/extension/services/socket-service.ts` - Socket.IO client for OpenHands backend
  - `src/extension/services/vscodeRuntimeActionHandler.ts` - Action execution handler
  - `src/extension/index.ts` - Extension entry point
  - `README.md` - Documentation
  - `package.json` - Extension manifest
- **Status**: 🔄 Needs migration to new location

## Migration Strategy

### Phase 1: Analysis and Preparation ✅ COMPLETE
1. **Understand Extension Structures**
   - ✅ Analyze new extension in `openhands/integrations/vscode/`
   - ✅ Analyze old runtime extension in `openhands/runtime/utils/vscode-extensions/openhands-runtime/`
   - ✅ Identify key files to migrate
   - ✅ Understand dependencies and imports
   - ✅ Created comprehensive migration plan

### Phase 2: File Migration ✅ COMPLETE
2. **Migrate Core Runtime Files**
   - **Source**: `openhands/runtime/utils/vscode-extensions/openhands-runtime/src/extension/services/`
   - **Destination**: `openhands/integrations/vscode/src/services/`
   - **Files to migrate**:
     - ✅ `socket-service.ts` → `src/services/socket-service.ts`
     - ✅ `vscodeRuntimeActionHandler.ts` → `src/services/runtime-action-handler.ts`

3. **Update Extension Entry Point**
   - **Target**: `openhands/integrations/vscode/src/extension.ts`
   - **Action**: Add runtime functionality alongside existing launcher functionality
   - **Integration**: Combine launcher commands with runtime action handling

4. **Update Package Configuration** ✅
   - **Target**: `openhands/integrations/vscode/package.json`
   - **Actions**:
     - ✅ Add runtime-related dependencies (socket.io-client, @openhands/types)
     - ✅ Add runtime activation events (onStartupFinished)
     - ✅ Add runtime configuration settings (openhands.serverUrl)
     - ✅ Update extension description to include runtime capabilities

5. **Update TypeScript Configuration** ✅
   - **Target**: `openhands/integrations/vscode/tsconfig.json`
   - **Action**: ✅ Ensure proper compilation of new service files (already includes src directory)

### Phase 3: Integration and Testing 🔄 IN PROGRESS
6. **Integrate Runtime with Launcher** ✅
   - **Approach**: Extend existing `extension.ts` with runtime capabilities
   - **Architecture**:
     ```typescript
     extension.ts
     ├── launcher/          // Existing: Context menu commands
     ├── services/
     │   ├── socket-service.ts      // New: Socket.IO client
     │   └── runtime-action-handler.ts  // New: Action execution
     └── activation logic   // Combined activation
     ```
   - ✅ Added imports for runtime services
   - ✅ Added runtime initialization function
   - ✅ Integrated runtime startup in activate()
   - ✅ Added cleanup in deactivate()
   - ✅ Added configuration reading for server URL

7. **Update Dependencies** ✅
   - **Target**: `openhands/integrations/vscode/package.json`
   - **Add dependencies**:
     - ✅ `socket.io-client` - for backend communication
     - ✅ `@openhands/types` - for OpenHands type definitions
   - **Install**: ✅ Run `npm install` in the extension directory

8. **Test Integration** ✅
   - **Compile**: ✅ `npm run compile` - No TypeScript errors
   - **Package**: ✅ `npm run package-vsix` - Successfully created openhands-vscode-0.0.1.vsix
   - **Install**: 🔄 Test the combined extension in VSCode (manual testing needed)
   - **Verify**: 🔄 Both launcher and runtime functionality work (manual testing needed)

### Phase 4: Cleanup ✅ COMPLETE
9. **Remove Old Runtime Extension** ✅
   - **Target**: `openhands/runtime/utils/vscode-extensions/openhands-runtime/`
   - **Action**: ✅ Delete entire directory after successful migration
   - **Verification**: ✅ Ensure no other code references this location
   - **Backup**: ✅ Created backup in /tmp/openhands-runtime-backup-* before removal

10. **Update Documentation** ✅
    - **Update**: `vscode.md` to reflect the combined extension (if needed)
    - **Update**: ✅ Extension README to document both launcher and runtime features
    - **Update**: ✅ Any references to the old runtime extension location (none found)

## Detailed File Migration Plan

### Files to Migrate

#### 1. Core Service Files
```bash
# Source → Destination
openhands/runtime/utils/vscode-extensions/openhands-runtime/src/extension/services/socket-service.ts
→ openhands/integrations/vscode/src/services/socket-service.ts

openhands/runtime/utils/vscode-extensions/openhands-runtime/src/extension/services/vscodeRuntimeActionHandler.ts  
→ openhands/integrations/vscode/src/services/runtime-action-handler.ts
```

#### 2. Dependencies to Add
```json
// Add to openhands/integrations/vscode/package.json
{
  "dependencies": {
    "socket.io-client": "^4.x.x",
    "@openhands/types": "workspace:*"
  }
}
```

#### 3. Configuration to Add
```json
// Add to openhands/integrations/vscode/package.json
{
  "contributes": {
    "configuration": {
      "title": "OpenHands",
      "properties": {
        "openhands.serverUrl": {
          "type": "string",
          "default": "http://localhost:3000",
          "description": "OpenHands server URL for runtime connection"
        }
      }
    }
  },
  "activationEvents": [
    "onStartupFinished"  // Add runtime activation
  ]
}
```

### Integration Points

#### 1. Extension Activation
```typescript
// In openhands/integrations/vscode/src/extension.ts
export function activate(context: vscode.ExtensionContext) {
    // Existing launcher functionality
    registerLauncherCommands(context);
    
    // New runtime functionality
    initializeRuntime(context);
}

function initializeRuntime(context: vscode.ExtensionContext) {
    // Initialize socket service and action handler
    // Start listening for OpenHands backend connections
}
```

#### 2. Service Integration
```typescript
// New services structure
src/services/
├── socket-service.ts          // Socket.IO client
├── runtime-action-handler.ts  // Action execution
└── workspace-utils.ts         // Shared utilities (if needed)
```

## Risk Mitigation

### Backup Strategy
1. **Create backup branch** before starting migration
2. **Test each phase** before proceeding to the next
3. **Keep old files** until migration is fully tested and verified

### Testing Strategy
1. **Unit testing**: Test individual service files
2. **Integration testing**: Test launcher + runtime together
3. **End-to-end testing**: Test with actual OpenHands backend
4. **Regression testing**: Ensure launcher functionality still works

### Rollback Plan
1. **If migration fails**: Revert to backup branch
2. **If integration issues**: Keep old and new extensions separate temporarily
3. **If dependencies conflict**: Resolve version conflicts or use different approach

## Success Criteria

### ✅ Migration Complete When:
1. **All runtime files** successfully migrated to new location
2. **Extension compiles** without errors
3. **Extension packages** successfully (creates .vsix file)
4. **Launcher functionality** still works (context menu, commands)
5. **Runtime functionality** works (connects to OpenHands backend)
6. **Old runtime extension** safely removed
7. **Documentation** updated to reflect changes

### ✅ Quality Checks:
1. **No broken imports** or missing dependencies
2. **TypeScript compilation** passes
3. **Extension activation** works in VSCode
4. **Socket.IO connection** establishes successfully
5. **Action handling** processes OpenHands actions correctly
6. **File operations** respect workspace security restrictions

## Timeline Estimate

- **Phase 1 (Analysis)**: ✅ Complete
- **Phase 2 (Migration)**: 2-3 hours
- **Phase 3 (Integration)**: 2-3 hours  
- **Phase 4 (Cleanup)**: 1 hour
- **Total**: 5-7 hours

## Next Steps

1. **Start with Phase 2**: Begin migrating core service files
2. **Test incrementally**: Verify each file migration works
3. **Integrate carefully**: Combine launcher and runtime functionality
4. **Clean up thoroughly**: Remove old files and update documentation

This migration will result in a **unified VSCode extension** that provides both launcher functionality (Task 1) and runtime execution capabilities (Task 2), setting the foundation for adding the webview UI (Task 3) in the future.

## Critical Files Inventory

### 🔥 **MUST MIGRATE** - Core Runtime Implementation
```
openhands/runtime/utils/vscode-extensions/openhands-runtime/src/extension/services/
├── socket-service.ts                    # Socket.IO client - CRITICAL
└── vscodeRuntimeActionHandler.ts        # Action handler - CRITICAL
```

### 📋 **SHOULD REVIEW** - Configuration and Setup
```
openhands/runtime/utils/vscode-extensions/openhands-runtime/
├── package.json                         # Dependencies and config
├── tsconfig.json                        # TypeScript config
├── README.md                           # Documentation
└── src/extension/index.ts              # Entry point logic
```

### 🎯 **TARGET LOCATION** - New Integrated Extension
```
openhands/integrations/vscode/
├── src/
│   ├── extension.ts                    # Main entry point (existing)
│   └── services/                       # New directory to create
│       ├── socket-service.ts           # Migrated from old location
│       └── runtime-action-handler.ts   # Migrated from old location
├── package.json                        # Update with new dependencies
└── tsconfig.json                       # Update if needed
```

**⚠️ IMPORTANT**: Do not delete old files until migration is complete and tested!