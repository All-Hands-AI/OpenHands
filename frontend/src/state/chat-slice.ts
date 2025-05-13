import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { Message } from "#/message";

type SliceState = {
  messages: Message[];
  systemMessage: {
    content: string;
    tools: Array<Record<string, unknown>> | null;
    openhands_version: string | null;
    agent_class: string | null;
  } | null;
};

const initialState: SliceState = {
  messages: [],
  systemMessage: null,
};

export const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addErrorMessage(
      state: SliceState,
      action: PayloadAction<{ id?: string; message: string }>,
    ) {
      const { id, message } = action.payload;
      state.messages.push({
        translationID: id,
        content: message,
        type: "error",
        sender: "assistant",
        timestamp: new Date().toISOString(),
      });
    },
  },
});

export const { addErrorMessage } = chatSlice.actions;

// Selectors
export const selectSystemMessage = (state: { chat: SliceState }) =>
  state.chat.systemMessage;

export default chatSlice.reducer;
