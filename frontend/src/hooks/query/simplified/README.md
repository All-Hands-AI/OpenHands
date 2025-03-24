# Simplified React Query Hooks

This directory contains simplified versions of the React Query hooks used in the Redux to React Query migration. These hooks provide the same API as the original hooks but use React's built-in state management (useState/useEffect) instead of React Query.

## Why Simplify?

Many of the hooks created during the Redux to React Query migration don't actually need the full power of React Query:

1. They don't fetch data from an API
2. They don't need caching
3. They don't need refetching
4. They're essentially just state containers

Using React Query for these simple state management cases adds unnecessary complexity and overhead.

## Benefits of Simplified Hooks

- **Smaller bundle size**: No need to include React Query for simple state management
- **Simpler code**: Easier to understand and maintain
- **Better performance**: No unnecessary query caching and management
- **Same API**: Drop-in replacements for the original hooks

## How to Use

### Option 1: Individual Hooks

Simply import the simplified hooks instead of the original hooks:

```tsx
// Instead of
import { useAgentState } from "#/hooks/query/use-agent-state";

// Use
import { useAgentState } from "#/hooks/query/simplified/use-agent-state";
```

The simplified hooks provide the same API as the original hooks, so no other changes are needed.

### Option 2: Context Provider (Recommended)

For better state sharing between components, use the context provider:

```tsx
// In your app root
import { AppStateProvider } from "#/hooks/query/simplified/use-state-context";

function App() {
  return (
    <AppStateProvider>
      {/* Your app components */}
    </AppStateProvider>
  );
}

// In your components
import { 
  useAgentState, 
  useMetrics, 
  useStatusMessage, 
  useInitialQuery 
} from "#/hooks/query/simplified/use-state-context";

function MyComponent() {
  const { curAgentState, setCurrentAgentState } = useAgentState();
  // Use the state and updater functions
}
```

The context provider approach has these advantages:
- Shared state between components
- No need to initialize from Redux in each component
- Consistent state updates across the app

## Hooks Available

- `useAgentState`: Manages agent state (loading, ready, etc.)
- `useMetrics`: Manages metrics data (cost, token usage)
- `useStatusMessage`: Manages status messages
- `useInitialQuery`: Manages initial query data (files, prompt, repository)

## When to Use React Query

React Query is still valuable for:

1. Fetching data from APIs
2. Caching server state
3. Managing loading/error states for network requests
4. Background refetching
5. Pagination and infinite scrolling

For these cases, continue using the original React Query hooks.