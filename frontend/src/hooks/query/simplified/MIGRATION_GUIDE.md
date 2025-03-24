# Migrating to Simplified Hooks

This guide explains how to migrate from React Query hooks to the simplified hooks.

## Step 1: Choose a Migration Strategy

You have two options for migration:

1. **Individual Hooks**: Replace each React Query hook with its simplified version
2. **Context Provider**: Use the context provider for shared state management

The context provider approach is recommended for better state sharing and consistency.

## Step 2: Set Up the Context Provider (If Using Option 2)

Add the `AppStateProvider` to your application root:

```tsx
// In src/entry.client.tsx or another root component
import { AppStateProvider } from "#/hooks/query/simplified/use-state-context";

// Wrap your app with the provider
function App() {
  return (
    <AppStateProvider>
      {/* Your app components */}
    </AppStateProvider>
  );
}
```

## Step 3: Replace Hook Imports

### Option 1: Individual Hooks

Replace each React Query hook import with its simplified version:

```tsx
// Before
import { useAgentState } from "#/hooks/query/use-agent-state";
import { useMetrics } from "#/hooks/query/use-metrics";
import { useStatusMessage } from "#/hooks/query/use-status-message";
import { useInitialQuery } from "#/hooks/query/use-initial-query";

// After
import { useAgentState } from "#/hooks/query/simplified/use-agent-state";
import { useMetrics } from "#/hooks/query/simplified/use-metrics";
import { useStatusMessage } from "#/hooks/query/simplified/use-status-message";
import { useInitialQuery } from "#/hooks/query/simplified/use-initial-query";
```

### Option 2: Context Provider

Import the hooks from the context provider:

```tsx
// Before
import { useAgentState } from "#/hooks/query/use-agent-state";
import { useMetrics } from "#/hooks/query/use-metrics";
import { useStatusMessage } from "#/hooks/query/use-status-message";
import { useInitialQuery } from "#/hooks/query/use-initial-query";

// After
import {
  useAgentState,
  useMetrics,
  useStatusMessage,
  useInitialQuery
} from "#/hooks/query/simplified/use-state-context";
```

## Step 4: Update the QueryReduxBridge

If you're using the context provider approach, you'll need to update the QueryReduxBridge to initialize the context provider with the Redux state.

Add this to your `query-redux-bridge-init.ts` file:

```tsx
import { AppStateProvider } from "#/hooks/query/simplified/use-state-context";

// In your initQueryReduxBridge function
export function initQueryReduxBridge(queryClient: QueryClient): QueryReduxBridge {
  queryReduxBridge = new QueryReduxBridge(queryClient);
  
  // Mark these slices as migrated to the simplified hooks
  queryReduxBridge.migrateSlice("agent");
  queryReduxBridge.migrateSlice("metrics");
  queryReduxBridge.migrateSlice("status");
  queryReduxBridge.migrateSlice("initialQuery");
  
  return queryReduxBridge;
}
```

## Step 5: Test Your Changes

Make sure everything works as expected:

1. Test that state is properly initialized from Redux
2. Test that state updates work correctly
3. Test that components using the hooks render correctly

## Example: Before and After

### Before (with React Query)

```tsx
import { useAgentState } from "#/hooks/query/use-agent-state";
import { AgentState } from "#/types/agent-state";

function AgentStatusComponent() {
  const { curAgentState, setCurrentAgentState } = useAgentState();
  
  return (
    <div>
      <p>Agent Status: {curAgentState}</p>
      <button onClick={() => setCurrentAgentState(AgentState.READY)}>
        Set Ready
      </button>
    </div>
  );
}
```

### After (with Simplified Hooks)

```tsx
import { useAgentState } from "#/hooks/query/simplified/use-state-context";
import { AgentState } from "#/types/agent-state";

function AgentStatusComponent() {
  const { curAgentState, setCurrentAgentState } = useAgentState();
  
  return (
    <div>
      <p>Agent Status: {curAgentState}</p>
      <button onClick={() => setCurrentAgentState(AgentState.READY)}>
        Set Ready
      </button>
    </div>
  );
}
```

The component code remains the same, only the import changes!