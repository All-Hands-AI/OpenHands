# ServerStatus vs AgentStatus Components Analysis

## Overview
Analysis of the differences between ServerStatus and AgentStatus components in `frontend/src/components/features/chat/custom-chat-input.tsx`.

## ServerStatus Component

### Purpose
Displays the overall server/conversation status and provides server control functionality.

### Location
`frontend/src/components/features/controls/server-status.tsx`

### Data Sources
- `curAgentState` from Redux state (`state.agent`)
- `conversationStatus` prop passed from parent component
- Uses mutation hooks for server control:
  - `useStartConversation`
  - `useStopConversation`
  - `useUserProviders`

### What it displays
- A colored dot indicator with status text
- Status text options:
  - "Starting" (when `AgentState.LOADING` or `AgentState.INIT`)
  - "Server Stopped" (when `AgentState.STOPPED` or `conversationStatus === "STOPPED"`)
  - "Error" (when `AgentState.ERROR`)
  - "Running" (default/normal state)

### Visual indicators
- **Yellow** (`#FFD600`): Starting state
- **White** (`#ffffff`): Stopped state
- **Red** (`#FF684E`): Error state
- **Green** (`#BCFF8C`): Running state

### Functionality
- Clickable to show a context menu for starting/stopping the server
- Provides server-level control (start/stop conversation)
- Context menu appears when conversation status is "RUNNING" or "STOPPED"

### Key Props
```typescript
interface ServerStatusProps {
  className?: string;
  conversationStatus: ConversationStatus | null;
}
```

## AgentStatus Component

### Purpose
Displays the agent's current working status and provides agent control functionality.

### Location
`frontend/src/components/features/controls/agent-status.tsx`

### Data Sources
- `curAgentState` from Redux state (`state.agent`)
- `curStatusMessage` from Redux state (`state.status`)
- `webSocketStatus` from WebSocket context (`useWsClient`)
- `conversation` data from `useActiveConversation` hook
- Uses `getStatusCode()` utility from `utils/status.ts` to determine status text

### What it displays
- Status text based on complex logic combining multiple states
- A circular button (24px) with different icons based on agent state:
  - **Loading spinner**: When initializing/loading (`AgentState.INIT`, `AgentState.LOADING`, or WebSocket connecting)
  - **Stop button**: When agent is running (`AgentState.RUNNING`)
  - **Play/Resume button**: When agent is stopped (`AgentState.STOPPED`)
  - **Error icon**: When there's an error (`AgentState.ERROR`, `AgentState.RATE_LIMITED`)
  - **Clock icon**: Default/fallback state

### Status Text Logic
Uses `getStatusCode()` function that considers:
1. Conversation status (STOPPED takes priority)
2. Runtime status
3. WebSocket connection status
4. Agent state via `AGENT_STATUS_MAP`

### Agent Status Mapping
```typescript
const AGENT_STATUS_MAP = {
  // Initializing states
  [AgentState.LOADING]: "Initializing",
  [AgentState.INIT]: "Initializing",
  
  // Ready/Idle/Waiting states
  [AgentState.AWAITING_USER_INPUT]: "Waiting for task",
  [AgentState.AWAITING_USER_CONFIRMATION]: "Waiting for task",
  [AgentState.FINISHED]: "Waiting for task",
  
  // Active states
  [AgentState.RUNNING]: "Running task",
  
  // Stopped states
  [AgentState.PAUSED]: "Agent stopped",
  [AgentState.STOPPED]: "Agent stopped",
  
  // Error states
  [AgentState.ERROR]: "Error occurred",
  [AgentState.RATE_LIMITED]: "Error occurred",
};
```

### Functionality
- Provides agent-level control (stop/resume agent)
- Interactive buttons for controlling agent execution
- Handles callbacks: `handleStop` and `handleResumeAgent`

### Key Props
```typescript
interface AgentStatusProps {
  className?: string;
  handleStop: () => void;
  handleResumeAgent: () => void;
  disabled?: boolean;
}
```

## Key Differences Summary

| Aspect | ServerStatus | AgentStatus |
|--------|-------------|-------------|
| **Scope** | Server/conversation level | Agent execution level |
| **Primary Data** | `curAgentState` + `conversationStatus` | Multiple sources via `getStatusCode()` |
| **UI Style** | Dot indicator + text | Text + interactive circular button |
| **Controls** | Start/stop server via context menu | Stop/resume agent via direct buttons |
| **Status Logic** | Simple status mapping | Complex multi-factor status determination |
| **Visual Feedback** | Color-coded dot | Icon-based button states |
| **Interaction** | Click → context menu | Direct button interaction |

## Usage in CustomChatInput

Both components are rendered in the bottom section of the chat input:

```tsx
<div className="w-full flex items-center justify-between">
  <div className="flex items-center gap-1">
    <Tools />
    <ServerStatus conversationStatus={conversationStatus} />
  </div>
  <AgentStatus
    handleStop={handleStop}
    handleResumeAgent={handleResumeAgent}
    disabled={disabled}
  />
</div>
```

- **ServerStatus**: Left side, shows overall system status
- **AgentStatus**: Right side, shows agent working status with controls

## Data Flow

### ServerStatus Data Flow
1. Parent passes `conversationStatus` prop
2. Component reads `curAgentState` from Redux
3. Simple logic determines color and text
4. Context menu provides server control actions

### AgentStatus Data Flow
1. Reads multiple Redux states (`agent`, `status`)
2. Gets WebSocket status from context
3. Fetches conversation data via TanStack Query
4. `getStatusCode()` utility processes all inputs
5. Component renders appropriate icon and handles user actions

## State Types

### AgentState Enum
```typescript
export enum AgentState {
  LOADING = "loading",
  INIT = "init",
  RUNNING = "running",
  AWAITING_USER_INPUT = "awaiting_user_input",
  PAUSED = "paused",
  STOPPED = "stopped",
  FINISHED = "finished",
  REJECTED = "rejected",
  ERROR = "error",
  RATE_LIMITED = "rate_limited",
  AWAITING_USER_CONFIRMATION = "awaiting_user_confirmation",
  USER_CONFIRMED = "user_confirmed",
  USER_REJECTED = "user_rejected",
}
```

### ConversationStatus Type
```typescript
export type ConversationStatus =
  | "STARTING"
  | "RUNNING"
  | "STOPPED"
  | "ARCHIVED"
  | "ERROR";
```

## Backend vs Frontend State Comparison

### AgentState Comparison

**Backend** (`openhands/core/schema/agent.py`):
```python
class AgentState(str, Enum):
    LOADING = 'loading'
    RUNNING = 'running'
    AWAITING_USER_INPUT = 'awaiting_user_input'
    PAUSED = 'paused'
    STOPPED = 'stopped'
    FINISHED = 'finished'
    REJECTED = 'rejected'
    ERROR = 'error'
    AWAITING_USER_CONFIRMATION = 'awaiting_user_confirmation'
    USER_CONFIRMED = 'user_confirmed'
    USER_REJECTED = 'user_rejected'
    RATE_LIMITED = 'rate_limited'
```

**Frontend** (`frontend/src/types/agent-state.tsx`):
```typescript
export enum AgentState {
  LOADING = "loading",
  INIT = "init",                    // ❌ MISSING IN BACKEND
  RUNNING = "running",
  AWAITING_USER_INPUT = "awaiting_user_input",
  PAUSED = "paused",
  STOPPED = "stopped",
  FINISHED = "finished",
  REJECTED = "rejected",
  ERROR = "error",
  RATE_LIMITED = "rate_limited",
  AWAITING_USER_CONFIRMATION = "awaiting_user_confirmation",
  USER_CONFIRMED = "user_confirmed",
  USER_REJECTED = "user_rejected",
}
```

### ConversationStatus Comparison

**Backend** (`openhands/storage/data_models/conversation_status.py`):
```python
class ConversationStatus(Enum):
    STARTING = 'STARTING'
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    ARCHIVED = 'ARCHIVED'
    ERROR = 'ERROR'
```

**Frontend** (`frontend/src/types/conversation-status.ts`):
```typescript
export type ConversationStatus =
  | "STARTING"
  | "RUNNING"
  | "STOPPED"
  | "ARCHIVED"
  | "ERROR";
```

### RuntimeStatus Comparison

**Backend** (`openhands/runtime/runtime_status.py`):
```python
class RuntimeStatus(Enum):
    STOPPED = 'STATUS$STOPPED'
    BUILDING_RUNTIME = 'STATUS$BUILDING_RUNTIME'
    STARTING_RUNTIME = 'STATUS$STARTING_RUNTIME'
    RUNTIME_STARTED = 'STATUS$RUNTIME_STARTED'
    SETTING_UP_WORKSPACE = 'STATUS$SETTING_UP_WORKSPACE'
    SETTING_UP_GIT_HOOKS = 'STATUS$SETTING_UP_GIT_HOOKS'
    READY = 'STATUS$READY'
    ERROR = 'STATUS$ERROR'
    ERROR_RUNTIME_DISCONNECTED = 'STATUS$ERROR_RUNTIME_DISCONNECTED'
    ERROR_LLM_AUTHENTICATION = 'STATUS$ERROR_LLM_AUTHENTICATION'
    ERROR_LLM_SERVICE_UNAVAILABLE = 'STATUS$ERROR_LLM_SERVICE_UNAVAILABLE'
    ERROR_LLM_INTERNAL_SERVER_ERROR = 'STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR'
    ERROR_LLM_OUT_OF_CREDITS = 'STATUS$ERROR_LLM_OUT_OF_CREDITS'
    ERROR_LLM_CONTENT_POLICY_VIOLATION = 'STATUS$ERROR_LLM_CONTENT_POLICY_VIOLATION'
    AGENT_RATE_LIMITED_STOPPED_MESSAGE = 'CHAT_INTERFACE$AGENT_RATE_LIMITED_STOPPED_MESSAGE'
    GIT_PROVIDER_AUTHENTICATION_ERROR = 'STATUS$GIT_PROVIDER_AUTHENTICATION_ERROR'
    LLM_RETRY = 'STATUS$LLM_RETRY'
    ERROR_MEMORY = 'STATUS$ERROR_MEMORY'
```

**Frontend** (`frontend/src/types/runtime-status.ts`):
```typescript
export type RuntimeStatus =
  | "STATUS$STOPPED"
  | "STATUS$BUILDING_RUNTIME"
  | "STATUS$STARTING_RUNTIME"
  | "STATUS$RUNTIME_STARTED"
  | "STATUS$SETTING_UP_WORKSPACE"
  | "STATUS$SETTING_UP_GIT_HOOKS"
  | "STATUS$READY"
  | "STATUS$ERROR"
  | "STATUS$ERROR_RUNTIME_DISCONNECTED"
  | "STATUS$ERROR_LLM_AUTHENTICATION"
  | "STATUS$ERROR_LLM_SERVICE_UNAVAILABLE"
  | "STATUS$ERROR_LLM_INTERNAL_SERVER_ERROR"
  | "STATUS$ERROR_LLM_OUT_OF_CREDITS"
  | "STATUS$ERROR_LLM_CONTENT_POLICY_VIOLATION"
  | "CHAT_INTERFACE$AGENT_RATE_LIMITED_STOPPED_MESSAGE"
  | "STATUS$GIT_PROVIDER_AUTHENTICATION_ERROR"
  | "STATUS$LLM_RETRY"
  | "STATUS$ERROR_MEMORY";
```

## Discrepancies Found

### ❌ Missing in Backend
1. **AgentState.INIT** - The frontend has `INIT = "init"` state but the backend doesn't define this state

### ✅ Perfectly Matched
1. **ConversationStatus** - All states match exactly between frontend and backend
2. **RuntimeStatus** - All states match exactly between frontend and backend

### Analysis
- The `INIT` state in the frontend appears to be used for initialization scenarios, particularly in the status logic where it's treated similarly to `LOADING`
- This suggests the frontend may be using `INIT` as a client-side state that doesn't correspond to an actual backend agent state
- The backend uses `LOADING` for initialization, while the frontend distinguishes between `INIT` and `LOADING`

### Recommendation
The `AgentState.INIT` should either be:
1. Added to the backend enum if it represents a valid agent state, or
2. Removed from the frontend if it's redundant with `LOADING`, or  
3. Documented as a frontend-only state if it serves a specific UI purpose