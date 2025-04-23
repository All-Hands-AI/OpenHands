# Agent Mode Toggle Design Document

## Overview

This document outlines the design for implementing a toggle switch between "Read-only mode" and "Execute mode" in the OpenHands application. This feature will allow users to switch between a restricted ReadOnlyAgent that can only explore and analyze code, and the fully capable CodeActAgent that can modify code and execute commands.

## Motivation

Users often want to explore a codebase and discuss implementation details with the agent before making any changes. The ability to switch between read-only and execute modes provides several benefits:

1. **Safety**: Users can ensure no changes are made during the exploration phase
2. **Clarity**: Clear indication of the agent's current capabilities
3. **Control**: Users decide when to transition from planning to execution
4. **Workflow**: Supports a natural workflow of exploration → planning → implementation

## Architecture

The implementation will leverage the existing agent delegation mechanism in OpenHands. When a user toggles the switch:

1. In **Execute Mode** (default): The application uses the standard CodeActAgent
2. In **Read-only Mode**: The application delegates to a ReadOnlyAgent

### Key Components

#### Frontend

1. **Toggle Switch Component**:
   - UI element that shows the current mode and allows switching
   - Sends appropriate actions to the event stream when toggled

2. **Agent State Tracking**:
   - Redux state to track current agent type and delegation status
   - Event listeners to update state based on event stream

3. **Visual Indicators**:
   - Mode indicator showing current agent mode
   - Visual styling differences between modes

#### Backend

1. **Agent Delegation**:
   - Uses existing delegation mechanism to switch to ReadOnlyAgent
   - User-initiated FinishAction to end delegation and return to CodeActAgent

2. **Event Stream Integration**:
   - AgentDelegateAction to start read-only mode
   - AgentFinishAction to end read-only mode
   - System messages to indicate mode changes

## Implementation Details

### Frontend Implementation

#### Redux State Extension

```typescript
interface AgentState {
  curAgentState: AgentState;
  currentAgentType: string; // Track the agent type
  isDelegated: boolean;     // Track if we're in a delegation
  // other existing fields...
}

const initialState: AgentState = {
  curAgentState: AgentState.IDLE,
  currentAgentType: "CodeActAgent", // Default agent type
  isDelegated: false,
  // other initial values...
};
```

#### Action Generators

```typescript
export const generateDelegateToReadOnlyAction = () => ({
  action: ActionType.DELEGATE,
  args: {
    agent: "ReadOnlyAgent",
    inputs: {
      task: "Continue the conversation in READ-ONLY MODE. You can explore and analyze code but cannot make changes."
    },
    thought: "Switching to read-only mode at user's request"
  }
});

export const generateFinishDelegationAction = () => ({
  action: ActionType.FINISH,
  args: {
    message: "Switching back to EXECUTE MODE. You now have full capabilities to modify code and execute commands.",
    task_completed: "true",
    outputs: {
      mode_switch: true
    }
  }
});
```

#### Toggle Switch Component

```tsx
function AgentModeToggle() {
  const { t } = useTranslation();
  const dispatch = useDispatch();
  const { send } = useWsClient();
  
  // Get agent type from Redux
  const { currentAgentType, isDelegated } = useSelector((state: RootState) => state.agent);
  
  // Compute if we're in read-only mode
  const isReadOnly = currentAgentType === "ReadOnlyAgent";
  
  const handleToggle = () => {
    if (isReadOnly) {
      // Currently in read-only mode, switch back to execute mode
      send(generateFinishDelegationAction());
    } else {
      // Currently in execute mode, switch to read-only mode
      send(generateDelegateToReadOnlyAction());
    }
  };
  
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm font-medium">
        {isReadOnly ? "Read-Only Mode" : "Execute Mode"}
      </span>
      <Switch 
        checked={isReadOnly} 
        onChange={handleToggle}
        className={`${isReadOnly ? 'bg-amber-600' : 'bg-blue-600'} relative inline-flex h-6 w-11 items-center rounded-full`}
      >
        <span className="sr-only">Toggle agent mode</span>
        <span
          className={`${isReadOnly ? 'translate-x-6' : 'translate-x-1'} inline-block h-4 w-4 transform rounded-full bg-white transition`}
        />
      </Switch>
    </div>
  );
}
```

#### Event Listener for State Updates

```typescript
function handleEvent(event) {
  // Handle agent delegation events
  if (event.action === ActionType.DELEGATE) {
    // A delegation is starting
    dispatch(setDelegationState(true));
    dispatch(setAgentType(event.args.agent));
  }
  
  // Handle agent delegate observation (delegation ended)
  else if (event.observation === "delegate") {
    // Delegation has ended, returning to parent agent
    dispatch(setDelegationState(false));
    dispatch(setAgentType("CodeActAgent")); // Reset to default agent
  }
  
  // Handle other events...
}
```

### Backend Considerations

The backend implementation will leverage the existing agent delegation mechanism:

1. When the user toggles to read-only mode:
   - An AgentDelegateAction is sent to the event stream
   - The AgentController creates a ReadOnlyAgent delegate
   - All subsequent events are handled by the delegate

2. When the user toggles back to execute mode:
   - An AgentFinishAction is sent to the event stream
   - The delegate agent finishes its task
   - The parent AgentController resumes normal operation

No backend code changes are required as we're using the existing delegation mechanism.

## User Experience

1. **Initial State**: The application starts in Execute Mode with CodeActAgent
2. **Mode Switching**:
   - User clicks the toggle switch to enter Read-only Mode
   - System message indicates the mode change
   - Agent capabilities are restricted to read-only tools
   - UI shows visual indicators of the current mode
   - User clicks the toggle switch again to return to Execute Mode
   - System message indicates the return to full capabilities

3. **Visual Indicators**:
   - Toggle switch position (left/right)
   - Color coding (amber for read-only, blue for execute)
   - Mode label text
   - System messages in the conversation

## Future Enhancements

1. **Persistent Mode Preference**: Remember the user's preferred starting mode
2. **Context Preservation**: Improve context retention when switching modes
3. **Custom Tool Sets**: Allow users to customize which tools are available in each mode
4. **Mode-specific Prompts**: Optimize agent prompts for each mode

## Implementation Plan

1. **Frontend Implementation**:
   - Add Redux state for agent type tracking
   - Create toggle switch component
   - Implement event listeners for state updates
   - Add visual indicators for current mode

2. **Testing**:
   - Test mode switching with various conversation states
   - Verify proper tool restrictions in read-only mode
   - Test persistence across page refreshes

3. **Documentation**:
   - Update user documentation to explain the mode toggle feature
   - Add developer documentation for the implementation details