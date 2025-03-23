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
import { useChatMessages } from "#/hooks/query/use-chat-messages";
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

// Example component that uses the migrated chat slice
function ChatComponent() {
  // Use the React Query hook for chat messages
  const { messages, addUserMessage, /* addAssistantMessage, */ clearMessages } =
    useChatMessages();

  const handleSendMessage = () => {
    addUserMessage({
      content: "Hello from React Query!",
      imageUrls: [],
      timestamp: new Date().toISOString(),
    });
  };

  const handleClearMessages = () => {
    clearMessages();
  };

  return (
    <div>
      <h2>Chat Messages</h2>
      <div
        style={{
          maxHeight: "300px",
          overflowY: "auto",
          border: "1px solid #ccc",
          padding: "10px",
          marginBottom: "10px",
        }}
      >
        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              marginBottom: "10px",
              textAlign: message.sender === "user" ? "right" : "left",
              padding: "8px",
              backgroundColor:
                message.sender === "user" ? "#e6f7ff" : "#f0f0f0",
              borderRadius: "8px",
            }}
          >
            <div>
              <strong>{message.sender}</strong>: {message.content}
            </div>
            <div style={{ fontSize: "0.8em", color: "#888" }}>
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
      <div>
        <button type="button" onClick={handleSendMessage}>
          Send Test Message
        </button>
        <button
          type="button"
          onClick={handleClearMessages}
          style={{ marginLeft: "10px" }}
        >
          Clear Messages
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
export function MigrationExample({
  conversationId,
}: {
  conversationId: string;
}) {
  // Mark the chat slice as migrated
  React.useEffect(() => {
    getQueryReduxBridge().migrateSlice("chat");
  }, []);

  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <WsClientProviderWithBridge conversationId={conversationId}>
          <WebSocketHandler />
          <div style={{ maxWidth: "800px", margin: "0 auto", padding: "20px" }}>
            <h1>Redux to React Query Migration Example</h1>
            <p>
              This example demonstrates how to migrate from Redux to React Query
              one slice at a time. The chat slice has been migrated to React
              Query, while other slices still use Redux.
            </p>
            <ChatComponent />
          </div>
        </WsClientProviderWithBridge>
      </QueryClientProvider>
    </Provider>
  );
}
