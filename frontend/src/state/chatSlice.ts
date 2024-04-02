import { createSlice } from "@reduxjs/toolkit";

export type Message = {
  content: string;
  sender: "user" | "assistant";
};

const initialMessages: Message[] = [];
const queuedMessages: number[] = [];
const currentQueueMarker: number = 0;
export const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: initialMessages,
    queuedTyping: queuedMessages,
    typingActive: false,
    currentTypingMessage: "",
    currentQueueMarker,
    userMessages: initialMessages,
    assistantMessages: initialMessages,
    newChatSequence: initialMessages,
  },
  reducers: {
    appendUserMessage: (state, action) => {
      state.messages.push({ content: action.payload, sender: "user" });
      state.userMessages.push({ content: action.payload, sender: "user" });
      state.newChatSequence.push({ content: action.payload, sender: "user" });
    },
    appendAssistantMessage: (state, action) => {
      state.messages.push({ content: action.payload, sender: "assistant" });
      state.assistantMessages.push({
        content: action.payload,
        sender: "assistant",
      });
      // state.queuedTyping.push(action.payload);
      const assistantMessageIndex = state.messages.length - 1;
      state.queuedTyping.push(assistantMessageIndex);
    },
    setCurrentQueueMarker: (state, action) => {
      state.currentQueueMarker = action.payload;
    },
    toggleTypingActive: (state, action) => {
      state.typingActive = action.payload;
    },
    emptyOutQueuedTyping: (state) => {
      state.queuedTyping = [];
    },
    setCurrentTypingMessage: (state, action) => {
      state.currentTypingMessage = action.payload;
      // state.currentQueueMarker += 1;
    },
    appeendToNewChatSequence: (state, action) => {
      state.newChatSequence.push(action.payload);
    },
  },
});

export const {
  appendUserMessage,
  appendAssistantMessage,
  toggleTypingActive,
  emptyOutQueuedTyping,
  setCurrentTypingMessage,
  setCurrentQueueMarker,
  appeendToNewChatSequence,
} = chatSlice.actions;

export default chatSlice.reducer;
