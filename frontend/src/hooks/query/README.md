# React Query Hooks

This directory contains hooks that use React's built-in state management (useState/useEffect) instead of React Query for simple state management.

## Simplified Hooks

The following hooks have been simplified to use React's built-in state management:

- `useAgentState`: Manages agent state (loading, ready, etc.)
- `useMetrics`: Manages metrics data (cost, token usage)
- `useStatusMessage`: Manages status messages
- `useInitialQuery`: Manages initial query data (files, prompt, repository)

These hooks don't need the full power of React Query because:
- They don't fetch data from an API
- They don't need caching
- They don't need refetching
- They're essentially just state containers

## Benefits of Simplified Hooks

- **Smaller bundle size**: No need to include React Query for simple state management
- **Simpler code**: Easier to understand and maintain
- **Better performance**: No unnecessary query caching and management
- **Same API**: The hooks provide the same API as before, so no changes are needed in components

## When to Use React Query

React Query is still valuable for:

1. Fetching data from APIs
2. Caching server state
3. Managing loading/error states for network requests
4. Background refetching
5. Pagination and infinite scrolling

For these cases, continue using React Query.