# React Redux to React Query Migration Plan

## Overview

This document outlines the step-by-step plan to migrate the OpenHands frontend from using Redux for state management to using React Query. The migration will focus on replacing Redux state management with React Query's data fetching and caching capabilities, while maintaining the application's functionality.

## Current State Analysis

### Redux Usage
- The application uses Redux Toolkit for state management
- Multiple slices are defined in the `/src/state` directory
- Redux is used for both server state (data fetching) and client state (UI state)
- Key slices include:
  - `chat-slice.ts`: Manages chat messages and interactions
  - `agent-slice.ts`: Manages agent state
  - `file-state-slice.ts`: Manages file explorer state
  - And several others for various features

### React Query Usage
- React Query is already implemented in the application
- Used primarily for data fetching in hooks under `/src/hooks/query`
- Examples include `use-list-files.ts`, `use-user-conversations.ts`, etc.
- Some hooks already combine React Query with Redux

## Migration Strategy

The migration will follow these principles:
1. **Incremental approach**: Migrate one slice at a time to minimize risk
2. **Server state first**: Focus on migrating Redux slices that manage server state first
3. **Client state last**: Keep UI-specific state in Redux until the end, then evaluate whether to use React Query, Context API, or other solutions
4. **Test-driven**: Write tests for each migration step to ensure functionality is preserved

## Step-by-Step Migration Plan

### Phase 1: Setup and Preparation

1. **Create React Query Provider Structure**
   - Enhance the existing React Query setup to support the expanded usage
   - Create a more robust error handling system for React Query
   - Set up proper devtools for React Query

2. **Create Shared Utilities**
   - Create utility functions for common React Query patterns
   - Set up custom hooks for common data fetching patterns

### Phase 2: Migrate Server State

3. **Migrate File Management State**
   - Create React Query hooks for file operations
   - Replace Redux file state with React Query
   - Update components to use the new hooks

4. **Migrate User Conversations State**
   - Create React Query hooks for conversation operations
   - Replace Redux conversation state with React Query
   - Update components to use the new hooks

5. **Migrate Configuration State**
   - Create React Query hooks for configuration
   - Replace Redux configuration state with React Query
   - Update components to use the new hooks

6. **Migrate GitHub Integration State**
   - Create React Query hooks for GitHub operations
   - Replace Redux GitHub state with React Query
   - Update components to use the new hooks

### Phase 3: Migrate Complex State

7. **Migrate Chat State**
   - This is more complex as it involves both server and client state
   - Create React Query mutations for sending messages
   - Create a custom hook for managing chat messages
   - Use React Query's cache to store message history
   - Update components to use the new hooks

8. **Migrate Agent State**
   - Create React Query hooks for agent operations
   - Create a custom hook for managing agent state
   - Update components to use the new hooks

9. **Migrate Terminal and Browser State**
   - Create React Query hooks for terminal and browser operations
   - Replace Redux terminal and browser state with React Query
   - Update components to use the new hooks

### Phase 4: Migrate Client-Only State

10. **Evaluate Client-Only State Needs**
    - For each remaining Redux slice, evaluate whether it should use:
      - React Query (for server-related state)
      - Context API (for shared UI state)
      - Component state (for localized UI state)

11. **Implement Client State Solutions**
    - Create appropriate context providers for shared UI state
    - Migrate remaining Redux slices to the chosen solution
    - Update components to use the new state management

### Phase 5: Cleanup and Optimization

12. **Remove Redux Dependencies**
    - Remove Redux-related code and dependencies
    - Clean up any unused imports or files

13. **Optimize React Query Usage**
    - Review and optimize query keys
    - Implement proper cache invalidation strategies
    - Add prefetching for common user flows

14. **Performance Testing**
    - Measure and compare performance before and after migration
    - Identify and fix any performance regressions

## Implementation Details

### New Directory Structure

```
/src
  /hooks
    /query       # Server state queries
    /mutation    # Server state mutations
    /state       # Client state hooks (replacing Redux)
  /context       # Context providers for shared state
  /utils
    /query       # React Query utilities
```

### Key Technical Approaches

1. **Query Keys Strategy**
   - Use consistent, hierarchical query keys
   - Example: `['files', conversationId, path]`
   - Document query key structure for team reference

2. **Optimistic Updates**
   - Implement optimistic updates for mutations
   - Example: When sending a message, optimistically add it to the UI

3. **Error Handling**
   - Centralized error handling through React Query's error callbacks
   - Custom error handling for specific queries when needed

4. **Websocket Integration**
   - Use React Query's cache to store websocket messages
   - Invalidate queries when receiving relevant websocket events

5. **Testing Strategy**
   - Unit tests for each new hook
   - Integration tests for components using the hooks
   - End-to-end tests for critical user flows

## Migration Sequence

The migration will proceed in the following order, with each step being completed, tested, and merged before moving to the next:

1. Setup and utilities (COMPLETED)
2. Simple server state (files, configurations) (COMPLETED)
3. User-related state (conversations, settings) (COMPLETED)
4. Complex state (chat, agent) (IN PROGRESS)
5. Client-only state
6. Cleanup and optimization

## Progress

### Completed
- Enhanced React Query setup with improved error handling and devtools
- Created utility functions for common React Query patterns
- Migrated file state to React Query context
- Migrated status state to React Query context
- Migrated metrics state to React Query context
- Migrated agent state to React Query context
- Migrated chat state to React Query context
- Migrated terminal state to React Query context
- Migrated browser state to React Query context

### In Progress
- Client-only state evaluation and migration

### Upcoming
- Redux cleanup and removal

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking changes during migration | Incremental approach with thorough testing at each step |
| Performance regressions | Performance testing before and after each migration step |
| Developer learning curve | Documentation and pair programming sessions |
| Websocket integration complexity | Create specialized hooks for websocket state |

## Success Criteria

The migration will be considered successful when:

1. All Redux dependencies are removed
2. All tests pass
3. No performance regressions are observed
4. The application functions identically to the pre-migration version
5. Code is cleaner and more maintainable
