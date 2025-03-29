import { describe, expect, it } from "vitest";
import { configureStore } from "@reduxjs/toolkit";
import chatReducer, {
  addAssistantMessage,
} from "#/state/chat-slice";

describe("chatSlice - addAssistantMessage", () => {
  it("adds an assistant message with correct content, agent name, and timestamp", () => {
    const store = configureStore({ reducer: { chat: chatReducer } });

    const content = "Test message";
    const agentName = "OpenHands";
    const timestamp = "2025-03-24T15:30:00Z";

    store.dispatch(
      addAssistantMessage({
        content: content,
        agentName: agentName,
        timestamp: timestamp
      }),
    );

    const state = store.getState().chat;
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0]).toEqual(
      expect.objectContaining({
        type: "thought",
        sender: "assistant",
        content,
        agentName,
        timestamp,
        imageUrls: [],
        pending: false,
      }),
    );
  });

  it("adds an assistant message with default timestamp when not provided", () => {
    const store = configureStore({ reducer: { chat: chatReducer } });

    const content = "Message without timestamp";
    const agentName = "AssistantAgent";

    store.dispatch(
      addAssistantMessage({
        content: content,
        agentName: agentName,
        timestamp: "",
      }),
    );

    const state = store.getState().chat;
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0]).toEqual(
      expect.objectContaining({
        type: "thought",
        sender: "assistant",
        content,
        agentName,
        timestamp: expect.any(String),
        imageUrls: [],
        pending: false,
      }),
    );
  });

  it("handles empty content and agent name correctly", () => {
    const store = configureStore({ reducer: { chat: chatReducer } });

    store.dispatch(
      addAssistantMessage({
        content: "",
        agentName: "",
        timestamp: "",
      }),
    );

    const state = store.getState().chat;
    expect(state.messages).toHaveLength(1);
    expect(state.messages[0]).toEqual(
      expect.objectContaining({
        type: "thought",
        sender: "assistant",
        content: "",
        agentName: "",
        timestamp: expect.any(String),
        imageUrls: [],
        pending: false,
      }),
    );
  });
});
