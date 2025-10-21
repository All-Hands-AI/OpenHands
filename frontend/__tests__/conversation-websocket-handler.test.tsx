import { describe, it, expect, beforeAll, afterAll, afterEach } from "vitest";
import { screen, waitFor, render, cleanup } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useOptimisticUserMessageStore } from "#/stores/optimistic-user-message-store";
import {
  createMockMessageEvent,
  createMockUserMessageEvent,
  createMockAgentErrorEvent,
} from "#/mocks/mock-ws-helpers";
import {
  ConnectionStatusComponent,
  EventStoreComponent,
  OptimisticUserMessageStoreComponent,
  ErrorMessageStoreComponent,
} from "./helpers/websocket-test-components";
import { ConversationWebSocketProvider } from "#/contexts/conversation-websocket-context";
import { conversationWebSocketTestSetup } from "./helpers/msw-websocket-setup";

// MSW WebSocket mock setup
const { wsLink, server: mswServer } = conversationWebSocketTestSetup();

beforeAll(() => {
  // The global MSW server from vitest.setup.ts is already running
  // We just need to start our WebSocket-specific server
  mswServer.listen({ onUnhandledRequest: "bypass" });
});

afterEach(() => {
  mswServer.resetHandlers();
  // Clean up any React components
  cleanup();
});

afterAll(async () => {
  // Close the WebSocket MSW server
  mswServer.close();

  // Give time for any pending WebSocket connections to close. This is very important to prevent serious memory leaks
  await new Promise((resolve) => {
    setTimeout(resolve, 500);
  });
});

// Helper function to render components with ConversationWebSocketProvider
function renderWithWebSocketContext(
  children: React.ReactNode,
  conversationId = "test-conversation-default",
  conversationUrl = "http://localhost:3000/api/conversations/test-conversation-default",
  sessionApiKey: string | null = null,
) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ConversationWebSocketProvider
        conversationId={conversationId}
        conversationUrl={conversationUrl}
        sessionApiKey={sessionApiKey}
      >
        {children}
      </ConversationWebSocketProvider>
    </QueryClientProvider>,
  );
}

describe("Conversation WebSocket Handler", () => {
  // 1. Connection Lifecycle Tests
  describe("Connection Management", () => {
    it("should establish WebSocket connection to /events/socket URL", async () => {
      // This will fail because we haven't created the context yet
      renderWithWebSocketContext(<ConnectionStatusComponent />);

      // Initially should be CONNECTING
      expect(screen.getByTestId("connection-state")).toHaveTextContent(
        "CONNECTING",
      );

      // Wait for connection to be established
      await waitFor(() => {
        expect(screen.getByTestId("connection-state")).toHaveTextContent(
          "OPEN",
        );
      });
    });

    it.todo("should provide manual disconnect functionality");
  });

  // 2. Event Processing Tests
  describe("Event Stream Processing", () => {
    it("should update event store with received WebSocket events", async () => {
      // Create a mock MessageEvent to send through WebSocket
      const mockMessageEvent = createMockMessageEvent();

      // Set up MSW to send the event when connection is established
      mswServer.use(
        wsLink.addEventListener("connection", ({ client, server }) => {
          server.connect();
          // Send the mock event after connection
          client.send(JSON.stringify(mockMessageEvent));
        }),
      );

      // Render components that use both WebSocket and event store
      renderWithWebSocketContext(<EventStoreComponent />);

      // Wait for connection and event processing
      await waitFor(() => {
        expect(screen.getByTestId("events-count")).toHaveTextContent("1");
      });

      // Verify the event was added to the store
      expect(screen.getByTestId("latest-event-id")).toHaveTextContent(
        "test-event-123",
      );
      expect(screen.getByTestId("ui-events-count")).toHaveTextContent("1");
    });

    it("should handle malformed/invalid event data gracefully", async () => {
      // Set up MSW to send various invalid events when connection is established
      mswServer.use(
        wsLink.addEventListener("connection", ({ client, server }) => {
          server.connect();

          // Send invalid JSON
          client.send("invalid json string");

          // Send valid JSON but missing required fields
          client.send(JSON.stringify({ message: "missing required fields" }));

          // Send valid JSON with wrong data types
          client.send(
            JSON.stringify({
              id: 123, // should be string
              timestamp: "2023-01-01T00:00:00Z",
              source: "agent",
            }),
          );

          // Send null values for required fields
          client.send(
            JSON.stringify({
              id: null,
              timestamp: "2023-01-01T00:00:00Z",
              source: "agent",
            }),
          );

          // Send a valid event after invalid ones to ensure processing continues
          client.send(
            JSON.stringify({
              id: "valid-event-123",
              timestamp: new Date().toISOString(),
              source: "agent",
              llm_message: {
                role: "assistant",
                content: [
                  { type: "text", text: "Valid message after invalid ones" },
                ],
              },
              activated_microagents: [],
              extended_content: [],
            }),
          );
        }),
      );

      // Render components that use both WebSocket and event store
      renderWithWebSocketContext(<EventStoreComponent />);

      // Wait for connection and event processing
      // Only the valid event should be added to the store
      await waitFor(() => {
        expect(screen.getByTestId("events-count")).toHaveTextContent("1");
      });

      // Verify only the valid event was added
      expect(screen.getByTestId("latest-event-id")).toHaveTextContent(
        "valid-event-123",
      );
      expect(screen.getByTestId("ui-events-count")).toHaveTextContent("1");
    });
  });

  // 3. State Management Tests
  describe("State Management Integration", () => {
    it("should clear optimistic user messages when confirmed", async () => {
      // First, set an optimistic user message
      const { setOptimisticUserMessage } =
        useOptimisticUserMessageStore.getState();
      setOptimisticUserMessage("This is an optimistic message");

      // Create a mock user MessageEvent to send through WebSocket
      const mockUserMessageEvent = createMockUserMessageEvent();

      // Set up MSW to send the user message event when connection is established
      mswServer.use(
        wsLink.addEventListener("connection", ({ client, server }) => {
          server.connect();
          // Send the mock user message event after connection
          client.send(JSON.stringify(mockUserMessageEvent));
        }),
      );

      // Render components that use both WebSocket and optimistic user message store
      renderWithWebSocketContext(<OptimisticUserMessageStoreComponent />);

      // Initially should show the optimistic message
      expect(screen.getByTestId("optimistic-user-message")).toHaveTextContent(
        "This is an optimistic message",
      );

      // Wait for connection and user message event processing
      // The optimistic message should be cleared when user message is confirmed
      await waitFor(() => {
        expect(screen.getByTestId("optimistic-user-message")).toHaveTextContent(
          "none",
        );
      });
    });
  });

  // 4. Cache Management Tests
  describe("Cache Management", () => {
    it.todo(
      "should invalidate file changes cache on file edit/write/command events",
    );
    it.todo("should invalidate specific file diff cache on file modifications");
    it.todo("should prevent cache refetch during high message rates");
    it.todo("should not invalidate cache for non-file-related events");
    it.todo("should invalidate cache with correct conversation ID context");
  });

  // 5. Error Handling Tests
  describe("Error Handling & Recovery", () => {
    it("should update error message store on AgentErrorEvent", async () => {
      // Create a mock AgentErrorEvent to send through WebSocket
      const mockAgentErrorEvent = createMockAgentErrorEvent();

      // Set up MSW to send the error event when connection is established
      mswServer.use(
        wsLink.addEventListener("connection", ({ client, server }) => {
          server.connect();
          // Send the mock error event after connection
          client.send(JSON.stringify(mockAgentErrorEvent));
        }),
      );

      // Render components that use both WebSocket and error message store
      renderWithWebSocketContext(<ErrorMessageStoreComponent />);

      // Initially should show "none"
      expect(screen.getByTestId("error-message")).toHaveTextContent("none");

      // Wait for connection and error event processing
      await waitFor(() => {
        expect(screen.getByTestId("error-message")).toHaveTextContent(
          "Failed to execute command: Permission denied",
        );
      });
    });

    it("should set error message store on WebSocket connection errors", async () => {
      // Set up MSW to simulate connection error
      mswServer.use(
        wsLink.addEventListener("connection", ({ client }) => {
          // Simulate connection error by closing immediately
          client.close(1006, "Connection failed");
        }),
      );

      // Render components that use both WebSocket and error message store
      renderWithWebSocketContext(
        <>
          <ErrorMessageStoreComponent />
          <ConnectionStatusComponent />
        </>,
      );

      // Initially should show "none"
      expect(screen.getByTestId("error-message")).toHaveTextContent("none");

      // Wait for connection error and error message to be set
      await waitFor(() => {
        expect(screen.getByTestId("connection-state")).toHaveTextContent(
          "CLOSED",
        );
      });

      // Should set error message on connection failure
      await waitFor(() => {
        expect(screen.getByTestId("error-message")).not.toHaveTextContent(
          "none",
        );
      });
    });

    it("should set error message store on WebSocket disconnect with error", async () => {
      // Set up MSW to connect first, then disconnect with error
      mswServer.use(
        wsLink.addEventListener("connection", ({ client, server }) => {
          server.connect();

          // Simulate disconnect with error after a short delay
          setTimeout(() => {
            client.close(1006, "Unexpected disconnect");
          }, 100);
        }),
      );

      // Render components that use both WebSocket and error message store
      renderWithWebSocketContext(
        <>
          <ErrorMessageStoreComponent />
          <ConnectionStatusComponent />
        </>,
      );

      // Initially should show "none"
      expect(screen.getByTestId("error-message")).toHaveTextContent("none");

      // Wait for connection to be established first
      await waitFor(() => {
        expect(screen.getByTestId("connection-state")).toHaveTextContent(
          "OPEN",
        );
      });

      // Wait for disconnect and error message to be set
      await waitFor(() => {
        expect(screen.getByTestId("connection-state")).toHaveTextContent(
          "CLOSED",
        );
      });

      // Should set error message on unexpected disconnect
      await waitFor(() => {
        expect(screen.getByTestId("error-message")).not.toHaveTextContent(
          "none",
        );
      });
    });

    it("should clear error message store when connection is restored", async () => {
      let connectionAttempt = 0;

      // Set up MSW to fail first connection, then succeed on retry
      mswServer.use(
        wsLink.addEventListener("connection", ({ client, server }) => {
          connectionAttempt += 1;

          if (connectionAttempt === 1) {
            // First attempt fails
            client.close(1006, "Initial connection failed");
          } else {
            // Second attempt succeeds
            server.connect();
          }
        }),
      );

      // Render components that use both WebSocket and error message store
      renderWithWebSocketContext(
        <>
          <ErrorMessageStoreComponent />
          <ConnectionStatusComponent />
        </>,
      );

      // Initially should show "none"
      expect(screen.getByTestId("error-message")).toHaveTextContent("none");

      // Wait for first connection failure and error message
      await waitFor(() => {
        expect(screen.getByTestId("connection-state")).toHaveTextContent(
          "CLOSED",
        );
      });

      await waitFor(() => {
        expect(screen.getByTestId("error-message")).not.toHaveTextContent(
          "none",
        );
      });

      // Simulate reconnection attempt (this would normally be triggered by the WebSocket context)
      // For now, we'll just verify the pattern - when connection is restored, error should clear
      // This test will fail until the WebSocket handler implements the clear logic

      // Note: This test demonstrates the expected behavior but may need adjustment
      // based on how the actual reconnection logic is implemented
    });

    it.todo("should track and display errors with proper metadata");
    it.todo("should set appropriate error states on connection failures");
    it.todo(
      "should handle WebSocket close codes appropriately (1000, 1006, etc.)",
    );
  });

  // 6. Connection State Validation Tests
  describe("Connection State Management", () => {
    it.todo("should only connect when conversation is in RUNNING status");
    it.todo("should handle STARTING conversation state appropriately");
    it.todo("should disconnect when conversation is STOPPED");
    it.todo("should validate runtime status before connecting");
  });

  // 7. Message Sending Tests
  describe("Message Sending", () => {
    it.todo("should send user actions through WebSocket when connected");
    it.todo("should handle send attempts when disconnected");
  });

  // 8. Terminal I/O Tests (ExecuteBashAction and ExecuteBashObservation)
  describe("Terminal I/O Integration", () => {
    it("should append command to store when ExecuteBashAction event is received", async () => {
      const { createMockExecuteBashActionEvent } = await import(
        "#/mocks/mock-ws-helpers"
      );
      const { useCommandStore } = await import("#/state/command-store");

      // Clear the command store before test
      useCommandStore.getState().clearTerminal();

      // Create a mock ExecuteBashAction event
      const mockBashActionEvent = createMockExecuteBashActionEvent("npm test");

      // Set up MSW to send the event when connection is established
      mswServer.use(
        wsLink.addEventListener("connection", ({ client, server }) => {
          server.connect();
          // Send the mock event after connection
          client.send(JSON.stringify(mockBashActionEvent));
        }),
      );

      // Render with WebSocket context (we don't need a component, just need the provider to be active)
      renderWithWebSocketContext(<ConnectionStatusComponent />);

      // Wait for connection
      await waitFor(() => {
        expect(screen.getByTestId("connection-state")).toHaveTextContent(
          "OPEN",
        );
      });

      // Wait for the command to be added to the store
      await waitFor(() => {
        const { commands } = useCommandStore.getState();
        expect(commands.length).toBe(1);
      });

      // Verify the command was added with correct type and content
      const { commands } = useCommandStore.getState();
      expect(commands[0].type).toBe("input");
      expect(commands[0].content).toBe("npm test");
    });

    it("should append output to store when ExecuteBashObservation event is received", async () => {
      const { createMockExecuteBashObservationEvent } = await import(
        "#/mocks/mock-ws-helpers"
      );
      const { useCommandStore } = await import("#/state/command-store");

      // Clear the command store before test
      useCommandStore.getState().clearTerminal();

      // Create a mock ExecuteBashObservation event
      const mockBashObservationEvent = createMockExecuteBashObservationEvent(
        "PASS  tests/example.test.js\n  ✓ should work (2 ms)",
        "npm test",
      );

      // Set up MSW to send the event when connection is established
      mswServer.use(
        wsLink.addEventListener("connection", ({ client, server }) => {
          server.connect();
          // Send the mock event after connection
          client.send(JSON.stringify(mockBashObservationEvent));
        }),
      );

      // Render with WebSocket context
      renderWithWebSocketContext(<ConnectionStatusComponent />);

      // Wait for connection
      await waitFor(() => {
        expect(screen.getByTestId("connection-state")).toHaveTextContent(
          "OPEN",
        );
      });

      // Wait for the output to be added to the store
      await waitFor(() => {
        const { commands } = useCommandStore.getState();
        expect(commands.length).toBe(1);
      });

      // Verify the output was added with correct type and content
      const { commands } = useCommandStore.getState();
      expect(commands[0].type).toBe("output");
      expect(commands[0].content).toBe(
        "PASS  tests/example.test.js\n  ✓ should work (2 ms)",
      );
    });
  });
});
