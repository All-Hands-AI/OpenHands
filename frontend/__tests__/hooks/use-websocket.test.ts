import { renderHook, waitFor } from "@testing-library/react";
import {
  describe,
  it,
  expect,
  beforeAll,
  afterAll,
  afterEach,
  vi,
} from "vitest";
import { ws } from "msw";
import { setupServer } from "msw/node";
import { useWebSocket } from "#/hooks/use-websocket";

// MSW WebSocket mock setup
const wsLink = ws.link("ws://acme.com/ws");

const server = setupServer(
  wsLink.addEventListener("connection", ({ client, server }) => {
    // Establish the connection
    server.connect();

    // Send a welcome message to confirm connection
    client.send("Welcome to the WebSocket!");
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("useWebSocket", () => {
  it("should establish a WebSocket connection", async () => {
    const { result } = renderHook(() => useWebSocket("ws://acme.com/ws"));

    // Initially should not be connected
    expect(result.current.isConnected).toBe(false);
    expect(result.current.lastMessage).toBe(null);

    // Wait for connection to be established
    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Should receive the welcome message from our mock
    await waitFor(() => {
      expect(result.current.lastMessage).toBe("Welcome to the WebSocket!");
    });

    // Confirm that the WebSocket connection is established when the hook is used
    expect(result.current.socket).toBeTruthy();
  });

  it("should handle incoming messages correctly", async () => {
    const { result } = renderHook(() => useWebSocket("ws://acme.com/ws"));

    // Wait for connection to be established
    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Should receive the welcome message from our mock
    await waitFor(() => {
      expect(result.current.lastMessage).toBe("Welcome to the WebSocket!");
    });

    // Send another message from the mock server
    wsLink.broadcast("Hello from server!");

    await waitFor(() => {
      expect(result.current.lastMessage).toBe("Hello from server!");
    });

    // Should have a messages array with all received messages
    expect(result.current.messages).toEqual([
      "Welcome to the WebSocket!",
      "Hello from server!",
    ]);
  });

  it("should handle connection errors gracefully", async () => {
    // Create a mock that will simulate an error
    const errorLink = ws.link("ws://error-test.com/ws");
    server.use(
      errorLink.addEventListener("connection", ({ client }) => {
        // Simulate an error by closing the connection immediately
        client.close(1006, "Connection failed");
      }),
    );

    const { result } = renderHook(() => useWebSocket("ws://error-test.com/ws"));

    // Initially should not be connected and no error
    expect(result.current.isConnected).toBe(false);
    expect(result.current.error).toBe(null);

    // Wait for the connection to fail
    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
    });

    // Should have error information (the close event should trigger error state)
    await waitFor(() => {
      expect(result.current.error).not.toBe(null);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    // Should have meaningful error message (could be from onerror or onclose)
    expect(
      result.current.error?.message.includes("WebSocket closed with code 1006"),
    ).toBe(true);

    // Should not crash the application
    expect(result.current.socket).toBeTruthy();
  });

  it("should close the WebSocket connection on unmount", async () => {
    const { result, unmount } = renderHook(() =>
      useWebSocket("ws://acme.com/ws"),
    );

    // Wait for connection to be established
    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Verify connection is active
    expect(result.current.isConnected).toBe(true);
    expect(result.current.socket).toBeTruthy();

    const closeSpy = vi.spyOn(result.current.socket!, "close");

    // Unmount the component (this should trigger the useEffect cleanup)
    unmount();

    // Verify that WebSocket close was called during cleanup
    expect(closeSpy).toHaveBeenCalledOnce();
  });

  it("should support query parameters in WebSocket URL", async () => {
    const baseUrl = "ws://acme.com/ws";
    const queryParams = {
      token: "abc123",
      userId: "user456",
      version: "v1",
    };

    const { result } = renderHook(() => useWebSocket(baseUrl, { queryParams }));

    // Wait for connection to be established
    await waitFor(() => {
      expect(result.current.isConnected).toBe(true);
    });

    // Verify that the WebSocket was created with query parameters
    expect(result.current.socket).toBeTruthy();
    expect(result.current.socket!.url).toBe(
      "ws://acme.com/ws?token=abc123&userId=user456&version=v1",
    );
  });
});
