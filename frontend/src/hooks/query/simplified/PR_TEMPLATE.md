# Simplified React Query Hooks

## Description

This PR introduces simplified alternatives to the React Query hooks created during the Redux to React Query migration. Many of the hooks don't actually need the full power of React Query and can be simplified to use React's built-in state management.

## Changes

- Added simplified versions of several hooks that don't need React Query:
  - `useAgentState`
  - `useMetrics`
  - `useStatusMessage`
  - `useInitialQuery`
- Added a context-based state management solution as an alternative
- Added documentation and tests

## Why This Change?

Many of the hooks created during the Redux to React Query migration don't actually need React Query's advanced features:
- They don't fetch data from an API
- They don't need caching
- They don't need refetching
- They're essentially just state containers

Using React Query for these simple state management cases adds unnecessary complexity and overhead.

## Benefits

- **Smaller bundle size**: No need to include React Query for simple state management
- **Simpler code**: Easier to understand and maintain
- **Better performance**: No unnecessary query caching and management
- **Same API**: Drop-in replacements for the original hooks

## How to Test

1. Run the tests: `cd frontend && npm run test -- -t "simplified"`
2. Try replacing one of the hooks in a component and verify it works the same

## Migration Strategy

This PR doesn't change any existing code - it just adds alternatives. Teams can gradually migrate to the simplified hooks as needed.

See the `MIGRATION_GUIDE.md` for detailed instructions on how to migrate.