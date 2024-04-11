import { createSlice } from "@reduxjs/toolkit";

export type Message = {
  content: string;
  sender: "user" | "assistant";
};

const initialMessages: Message[] = [
  {
    content:
      "Hi! I'm OpenDevin, an AI Software Engineer. What would you like to build with me today?",
    sender: "assistant",
  },
];
export const chatSlice = createSlice({
  name: "chat",
  initialState: {
    messages: initialMessages,
    typingActive: false,
    userMessages: initialMessages,
    assistantMessages: initialMessages,
    assistantMessagesTypingQueue: [] as Message[],
    newChatSequence: initialMessages,
    typeThis: { content: "", sender: "assistant" } as Message,
  },
  reducers: {
    appendUserMessage: (state, action) => {
      state.messages.push({ content: action.payload, sender: "user" });
      state.userMessages.push({ content: action.payload, sender: "user" });
      state.newChatSequence.push({ content: action.payload, sender: "user" });
    },
    appendAssistantMessage: (state, action) => {
      state.messages.push({ content: action.payload, sender: "assistant" });

      if (
        state.assistantMessagesTypingQueue.length > 0 ||
        state.typingActive === true
      ) {
        state.assistantMessagesTypingQueue.push({
          content: action.payload,
          sender: "assistant",
        });
      } else if (
        state.assistantMessagesTypingQueue.length === 0 &&
        state.typingActive === false
      ) {
        state.typeThis = {
          content: action.payload,
          sender: "assistant",
        };
        state.typingActive = true;
      }
    },

    toggleTypingActive: (state, action) => {
      state.typingActive = action.payload;
    },

    appendToNewChatSequence: (state, action) => {
      state.newChatSequence.push(action.payload);
    },

    takeOneTypeIt: (state) => {
      if (state.assistantMessagesTypingQueue.length > 0) {
        state.typeThis = state.assistantMessagesTypingQueue.shift() as Message;
      }
    },
  },
});

export const {
  appendUserMessage,
  appendAssistantMessage,
  toggleTypingActive,
  appendToNewChatSequence,
  takeOneTypeIt,
} = chatSlice.actions;

export default chatSlice.reducer;
