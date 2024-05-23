import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type SliceState = { messages: Message[] };

const initialState: SliceState = {
  messages: [],
};

export const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addUserMessage(state, action: PayloadAction<string>) {
      const message: Message = {
        sender: "user",
        content: action.payload,
      };

      state.messages.push(message);
    },

    addAssistantMessage(state, action: PayloadAction<string>) {
      const message: Message = {
        sender: "assistant",
        content: action.payload,
      };

      state.messages.push(message);
    },

    clearMessages(state) {
      state.messages = [];
    },
  },
});

export const { addUserMessage, addAssistantMessage, clearMessages } =
  chatSlice.actions;
export default chatSlice.reducer;
