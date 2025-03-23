import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Provider } from "react-redux";
import store from "#/store";
import {
  initQueryReduxBridge,
  getQueryReduxBridge,
} from "#/utils/query-redux-bridge";
import { WsClientProviderWithBridge } from "#/context/ws-client-provider-with-bridge";
import { useWebsocketEvents } from "#/hooks/query/use-websocket-events";
import { useStatusMessage } from "#/hooks/query/use-status-message";
import { queryClientConfig } from "#/query-client-config";

// Create a query client
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

// Example component that uses the migrated status slice
function StatusComponent() {
  // Use the React Query hook for status messages
  const { statusMessage, setStatusMessage } = useStatusMessage();

  const handleSetInfoStatus = () => {
    setStatusMessage({
      status_update: true,
      type: "info",
      id: `info-${Date.now()}`,
      message: "This is an info message from React Query!",
    });
  };

  const handleSetErrorStatus = () => {
    setStatusMessage({
      status_update: true,
      type: "error",
      id: `error-${Date.now()}`,
      message: "This is an error message from React Query!",
    });
  };

  return (
    <div>
      <h2>Status Message</h2>
      <div
        style={{
          padding: "15px",
          border: "1px solid #ccc",
          borderRadius: "5px",
          marginBottom: "15px",
          backgroundColor:
            statusMessage.type === "error" ? "#ffebee" : "#e3f2fd",
        }}
      >
        <div>
          <strong>Type:</strong> {statusMessage.type}
        </div>
        <div>
          <strong>ID:</strong> {statusMessage.id}
        </div>
        <div>
          <strong>Message:</strong> {statusMessage.message}
        </div>
      </div>
      <div>
        <button
          type="button"
          onClick={handleSetInfoStatus}
          style={{ marginRight: "10px", padding: "8px 16px" }}
        >
          Set Info Status
        </button>
        <button
          type="button"
          onClick={handleSetErrorStatus}
          style={{ padding: "8px 16px" }}
        >
          Set Error Status
        </button>
      </div>
    </div>
  );
}

// Component that handles websocket events
function WebSocketHandler() {
  // This hook will process websocket events for React Query
  useWebsocketEvents();
  return null;
}

// Main application component
export function StatusSliceMigrationExample({
  conversationId,
}: {
  conversationId: string;
}) {
  // Mark the status slice as migrated
  React.useEffect(() => {
    getQueryReduxBridge().migrateSlice("status");
  }, []);

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <WsClientProviderWithBridge conversationId={conversationId}>
          <WebSocketHandler />
          <div style={{ maxWidth: "800px", margin: "0 auto", padding: "20px" }}>
            <h1>Status Slice Migration Example</h1>
            <p>
              This example demonstrates how to migrate the status slice from
              Redux to React Query. The status slice has been migrated to React
              Query, while other slices still use Redux.
            </p>
            <StatusComponent />
          </div>
        </WsClientProviderWithBridge>
      </QueryClientProvider>
    </Provider>
  );
}
