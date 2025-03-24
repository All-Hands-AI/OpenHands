# Redux to React Query Migration Guide

This guide outlines the process for migrating from Redux to React Query in our application.

## Overview

The migration strategy allows for a gradual transition from Redux to React Query, with the ability to migrate one slice at a time without breaking the application. This is achieved through a bridge that coordinates between Redux and React Query.

## Key Components

1. **QueryReduxBridge**: A utility class that manages the migration state and coordinates between Redux and React Query.
2. **Websocket Integration**: Modified to respect migration flags and update the appropriate state management system.
3. **React Query Hooks**: New hooks that replace Redux slice functionality.

## Migration Steps

### 1. Initialize the Bridge

In your main application file (e.g., `App.tsx`), initialize the bridge:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { initQueryReduxBridge } from '#/utils/query-redux-bridge';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
  ...queryClientConfig,
});

// Initialize the bridge
initQueryReduxBridge(queryClient);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {/* Your app components */}
    </QueryClientProvider>
  );
}
```

### 2. Replace the WebSocket Provider

Replace the original WebSocket provider with the bridge-aware version:

```tsx
import { WsClientProviderWithBridge } from '#/context/ws-client-provider-with-bridge';

// Instead of
// <WsClientProvider conversationId={conversationId}>
//   {children}
// </WsClientProvider>

// Use
<WsClientProviderWithBridge conversationId={conversationId}>
  {children}
</WsClientProviderWithBridge>
```

### 3. Add the WebSocket Events Hook

Add the WebSocket events hook to your application to handle events for React Query:

```tsx
import { useWebsocketEvents } from '#/hooks/query/use-websocket-events';

function YourComponent() {
  // This hook will process websocket events for React Query
  useWebsocketEvents();

  // Rest of your component
  return (
    // ...
  );
}
```

### 4. Migrate Individual Slices

For each Redux slice you want to migrate:

1. Create a React Query hook that replaces the slice functionality
2. Mark the slice as migrated
3. Update components to use the new hook instead of Redux

Example for migrating the chat slice:

```tsx
import { useChatMessages } from '#/hooks/query/use-chat-messages';
import { getQueryReduxBridge } from '#/utils/query-redux-bridge';

// Mark the slice as migrated
getQueryReduxBridge().migrateSlice('chat');

function ChatComponent() {
  // Instead of using useSelector and useDispatch
  // const messages = useSelector((state) => state.chat.messages);
  // const dispatch = useDispatch();

  // Use the React Query hook
  const {
    messages,
    addUserMessage,
    addAssistantMessage,
    addErrorMessage,
    clearMessages
  } = useChatMessages();

  // Rest of your component using the new API
  return (
    // ...
  );
}
```

## Testing the Migration

To test the migration of a single slice:

1. Create the React Query hook for the slice
2. Mark the slice as migrated using `getQueryReduxBridge().migrateSlice('sliceName')`
3. Update a single component to use the new hook
4. Test the application to ensure it works correctly
5. If issues arise, you can easily revert by removing the migration flag

## Troubleshooting

### Duplicate Updates

If you see duplicate updates (e.g., chat messages appearing twice), check:

1. Ensure you're using the bridge-aware WebSocket provider
2. Verify the slice is properly marked as migrated
3. Check that components aren't mixing Redux and React Query for the same slice

### Console Errors

If you encounter console errors:

1. Check for race conditions between Redux and React Query
2. Ensure the WebSocket events hook is properly mounted
3. Verify that the QueryReduxBridge is initialized before any components try to use it

## Complete Migration

Once all slices are migrated:

1. Remove the Redux store and related code
2. Simplify the bridge code to remove Redux dependencies
3. Update the WebSocket provider to directly update React Query without the bridge
