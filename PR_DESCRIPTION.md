# Simplified React Query Hooks

## Description

This PR introduces simplified alternatives to the React Query hooks created during the Redux to React Query migration. Many of the hooks don't actually need the full power of React Query and can be simplified to use React's built-in state management.

## Problem

During the Redux to React Query migration, many hooks were created that don't actually need React Query's advanced features:
- They don't fetch data from an API
- They don't need caching
- They don't need refetching
- They're essentially just state containers

Using React Query for these simple state management cases adds unnecessary complexity and overhead.

## Solution

This PR provides:

1. **Individual Simplified Hooks**:
   - `useAgentState`: Manages agent state (loading, ready, etc.)
   - `useMetrics`: Manages metrics data (cost, token usage)
   - `useStatusMessage`: Manages status messages
   - `useInitialQuery`: Manages initial query data (files, prompt, repository)

2. **Context-Based State Management**:
   - A context provider for shared state management
   - Exports the same hooks as above, but with shared state

3. **Documentation**:
   - README explaining the purpose and benefits of simplified hooks
   - Migration guide for transitioning to simplified hooks

## Benefits

- **Smaller bundle size**: No need to include React Query for simple state management
- **Simpler code**: Easier to understand and maintain
- **Better performance**: No unnecessary query caching and management
- **Same API**: Drop-in replacements for the original hooks

## Implementation

The implementation:
1. Creates simplified hooks that match the API of the original hooks
2. Provides a context provider for better state sharing
3. Updates a few components to use the simplified hooks
4. Adds the context provider to the application root

## Testing

The PR includes tests for:
1. Individual simplified hooks
2. The context provider

## Next Steps

After this PR is merged, we can:
1. Gradually migrate more components to use the simplified hooks
2. Remove unnecessary React Query dependencies
3. Simplify the bridge code