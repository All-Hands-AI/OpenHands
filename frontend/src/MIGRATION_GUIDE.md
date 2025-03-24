# Redux to React Query Migration Guide

This document outlines the completed migration from Redux to React Query in our application.

## Overview

The application has been fully migrated from Redux to React Query. All state management is now handled by React Query, and Redux dependencies have been removed.

## Key Components

1. **QueryClientWrapper**: A utility class that provides a simplified API for managing state with React Query.
2. **React Query Hooks**: Custom hooks that provide state management functionality for different parts of the application.

## Architecture

The application now uses a pure React Query architecture:

1. **State Management**: All state is managed through React Query's cache
2. **Data Fetching**: API calls are handled through React Query's query and mutation hooks
3. **Real-time Updates**: WebSocket events update the React Query cache directly

## Using React Query in the Application

### 1. Initialize the Query Client

The query client is initialized in `query-redux-bridge-init.ts`:

```tsx
import { QueryClient } from '@tanstack/react-query';
import { queryClientConfig } from './query-client-config';

// Create a query client
export const queryClient = new QueryClient(queryClientConfig);

// Initialize the client wrapper
export function initializeBridge() {
  initQueryReduxBridge(queryClient);
}
```

### 2. Use React Query Hooks

Each feature has its own custom hook that provides state management:

```tsx
import { useChat } from '#/hooks/query/use-chat';

function ChatComponent() {
  const { 
    messages, 
    addUserMessage, 
    addAssistantMessage, 
    addErrorMessage, 
    clearMessages 
  } = useChat();
  
  // Use the hook's methods and state
  return (
    // ...
  );
}
```

### 3. WebSocket Integration

WebSocket events are processed and update the React Query cache directly:

```tsx
import { useQueryClient } from '@tanstack/react-query';

function processWebSocketEvent(event) {
  const queryClient = useQueryClient();
  
  // Update the appropriate query data
  queryClient.setQueryData(['queryKey'], newData);
}
```

## Benefits of the Migration

1. **Simplified State Management**: React Query handles caching, refetching, and background updates
2. **Reduced Boilerplate**: No need for actions, reducers, and selectors
3. **Improved Performance**: Automatic request deduplication and caching
4. **Better Developer Experience**: Hooks-based API is more intuitive and easier to use
5. **Smaller Bundle Size**: Removed Redux dependencies reduce the application size