# Redux to React Query Migration Simplification

## Overview

This directory contains simplified alternatives to the React Query hooks created during the Redux to React Query migration. The goal is to provide simpler, more efficient state management for hooks that don't need the full power of React Query.

## What We've Created

1. **Individual Simplified Hooks**:
   - `useAgentState`: Manages agent state (loading, ready, etc.)
   - `useMetrics`: Manages metrics data (cost, token usage)
   - `useStatusMessage`: Manages status messages
   - `useInitialQuery`: Manages initial query data (files, prompt, repository)

2. **Context-Based State Management**:
   - `use-state-context.tsx`: Provides a context-based approach to state management
   - Exports the same hooks as above, but with shared state

3. **Documentation**:
   - `README.md`: Explains the purpose and benefits of simplified hooks
   - `MIGRATION_GUIDE.md`: Step-by-step guide for migrating to simplified hooks

4. **Tests**:
   - Tests for individual hooks
   - Tests for the context provider

## Recommendations

After analyzing the Redux to React Query migration, we recommend:

1. **Use the Context Provider Approach**:
   - Provides shared state between components
   - Simpler implementation than React Query for basic state
   - Same API as the original hooks for easy migration

2. **Keep React Query for API Interactions**:
   - Continue using React Query for hooks that interact with APIs
   - Keep React Query for hooks that need caching, refetching, etc.

3. **Gradual Migration**:
   - Start with simple state hooks (agent state, metrics, status message)
   - Move to more complex hooks as needed

## Hooks That Don't Need React Query

The following hooks don't really need React Query and can be simplified:

1. `useAgentState`: Just tracks a simple enum state
2. `useMetrics`: Just tracks cost and usage data
3. `useStatusMessage`: Just tracks a status message
4. `useInitialQuery`: Just tracks files, initialPrompt, and selectedRepository

## Hooks That Benefit from React Query

The following hooks benefit from React Query and should keep using it:

1. Hooks that fetch data from APIs
2. Hooks that need caching
3. Hooks that need background refetching
4. Hooks that manage complex server state

## Next Steps

1. Review the simplified hooks and context provider
2. Decide on a migration strategy (individual hooks or context provider)
3. Start migrating simple hooks first
4. Test thoroughly to ensure everything works as expected