import { createSlice } from "@reduxjs/toolkit";

type Message = {
  content: string;
  sender: "user" | "assistant";
};

const initialMessages: Message[] = [];

export const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: initialMessages,
  },
  reducers: {
    appendUserMessage: (state, action) => {
      state.messages.push({ content: action.payload, sender: "user" });
    },
    appendAssistantMessage: (state, action) => {
      state.messages.push({ content: action.payload, sender: "assistant" });
    },
  },
});

export const { appendUserMessage, appendAssistantMessage } = chatSlice.actions;

export default chatSlice.reducer;
