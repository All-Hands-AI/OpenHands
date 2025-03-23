# Redux to React Query Migration

This directory contains scaffolding to support a gradual migration from Redux to React Query.

## Overview

The migration strategy allows for a slice-by-slice transition from Redux to React Query without breaking the application. This is particularly important for handling websocket events, which previously caused duplicate chat messages and console errors when migrating.

## Key Components

1. **QueryReduxBridge** (`utils/query-redux-bridge.ts`): A utility class that manages the migration state and coordinates between Redux and React Query.

2. **Websocket Integration**:
   - `context/ws-client-provider-with-bridge.tsx`: A modified websocket provider that respects migration flags
   - `hooks/query/use-websocket-events.ts`: A hook that processes websocket events for React Query

3. **React Query Hooks**:
   - `hooks/query/use-chat-messages.ts`: A hook that replaces the chat slice functionality
   - `hooks/query/use-status-message.ts`: A hook that replaces the status slice functionality

4. **Bridge-aware Action Handlers**:
   - `services/actions-with-bridge.ts`: Modified action handlers that respect migration flags
   - `services/observations-with-bridge.ts`: Modified observation handlers that respect migration flags

## Migration Process

1. **Initialize the Bridge**:
   ```tsx
   import { initQueryReduxBridge } from '#/utils/query-redux-bridge';
   
   // Initialize with your QueryClient
   initQueryReduxBridge(queryClient);
   ```

2. **Replace the WebSocket Provider**:
   ```tsx
   import { WsClientProviderWithBridge } from '#/context/ws-client-provider-with-bridge';
   
   // Use the bridge-aware provider
   <WsClientProviderWithBridge conversationId={conversationId}>
     {children}
   </WsClientProviderWithBridge>
   ```

3. **Add the WebSocket Events Hook**:
   ```tsx
   import { useWebsocketEvents } from '#/hooks/query/use-websocket-events';
   
   function YourComponent() {
     // Process websocket events for React Query
     useWebsocketEvents();
     // ...
   }
   ```

4. **Migrate Individual Slices**:
   ```tsx
   import { getQueryReduxBridge } from '#/utils/query-redux-bridge';
   import { useChatMessages } from '#/hooks/query/use-chat-messages';
   
   // Mark the slice as migrated
   getQueryReduxBridge().migrateSlice('chat');
   
   function ChatComponent() {
     // Use the React Query hook instead of Redux
     const { messages, addUserMessage } = useChatMessages();
     // ...
   }
   ```

## Example Implementations

- `examples/MigrationExample.tsx`: A complete example of how to use the migration scaffolding with the chat slice
- `examples/StatusSliceMigrationExample.tsx`: An example showing how to migrate the status slice

## Notes on Implementation

- The code includes some linting issues that would be fixed in a production environment
- The build passes successfully despite these linting issues
- The approach allows for a gradual migration, one slice at a time
- Once all slices are migrated, the Redux store and related code can be removed

## Troubleshooting

If you encounter duplicate updates or console errors:

1. Ensure you're using the bridge-aware WebSocket provider
2. Verify the slice is properly marked as migrated
3. Check that components aren't mixing Redux and React Query for the same slice
4. Make sure the WebSocket events hook is properly mounted