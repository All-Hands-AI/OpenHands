# React Query Hooks

This directory contains hooks that use React Query to manage state in the application. However, not all hooks need the full power of React Query.

## Simplified Hooks

For hooks that don't need the full power of React Query (e.g., they don't fetch data from an API, don't need caching, etc.), we've created simplified versions in the `simplified` directory.

The simplified hooks provide the same API as the original hooks but use React's built-in state management (useState/useEffect) instead of React Query.

### Benefits of Simplified Hooks

- **Smaller bundle size**: No need to include React Query for simple state management
- **Simpler code**: Easier to understand and maintain
- **Better performance**: No unnecessary query caching and management
- **Same API**: Drop-in replacements for the original hooks

### How to Use

Simply import the simplified hooks instead of the original hooks:

```tsx
// Instead of
import { useAgentState } from "#/hooks/query/use-agent-state";

// Use
import { useAgentState } from "#/hooks/query/simplified/use-agent-state";
```

### Context Provider

For better state sharing between components, we've also created a context provider:

```tsx
import { 
  useAgentState, 
  useMetrics, 
  useStatusMessage, 
  useInitialQuery 
} from "#/hooks/query/simplified/use-state-context";
```

The context provider is already set up in the application root, so you can use these hooks anywhere in the application.

## When to Use React Query

React Query is still valuable for:

1. Fetching data from APIs
2. Caching server state
3. Managing loading/error states for network requests
4. Background refetching
5. Pagination and infinite scrolling

For these cases, continue using the original React Query hooks.

## Hooks That Don't Need React Query

The following hooks don't really need React Query and have been simplified:

1. `useAgentState`: Just tracks a simple enum state
2. `useMetrics`: Just tracks cost and usage data
3. `useStatusMessage`: Just tracks a status message
4. `useInitialQuery`: Just tracks files, initialPrompt, and selectedRepository

## Hooks That Benefit from React Query

The following hooks benefit from React Query and should keep using it:

1. Hooks that fetch data from APIs (e.g., `useUserConversation`, `useSettings`)
2. Hooks that need caching (e.g., `useChat`, `useCommand`)
3. Hooks that need background refetching (e.g., `useActiveHost`)
4. Hooks that manage complex server state (e.g., `useFileState`, `useJupyter`)