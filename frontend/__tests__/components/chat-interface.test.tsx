import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { SocketContext } from "#/context/socket";
import { ChatInterface } from "#/components/chat-interface";
import chatReducer from "#/state/chatSlice";
import agentReducer from "#/state/agentSlice";
import { describe, it, expect, vi } from "vitest";

describe("ChatInterface", () => {
  const mockStore = configureStore({
    reducer: {
      chat: chatReducer,
      agent: agentReducer,
    },
  });

  const mockSocket = {
    send: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    setRuntimeIsInitialized: vi.fn(),
    runtimeActive: false,
    isConnected: false,
    events: [],
  };

  const renderWithProviders = (isConnected = false) => {
    return render(
      <Provider store={mockStore}>
        <SocketContext.Provider value={{ ...mockSocket, isConnected }}>
          <ChatInterface />
        </SocketContext.Provider>
      </Provider>
    );
  };

  it("should not show empty state UI when socket is not connected", () => {
    renderWithProviders(false);
    expect(screen.queryByText("Let's start building!")).not.toBeInTheDocument();
  });

  it("should show empty state UI when socket is connected and no messages", () => {
    renderWithProviders(true);
    expect(screen.getByText("Let's start building!")).toBeInTheDocument();
  });

  it("should not show empty state UI when there are messages", () => {
    mockStore.dispatch({
      type: "chat/addUserMessage",
      payload: {
        content: "Test message",
        imageUrls: [],
        timestamp: new Date().toISOString(),
      },
    });
    renderWithProviders(true);
    expect(screen.queryByText("Let's start building!")).not.toBeInTheDocument();
  });
});
