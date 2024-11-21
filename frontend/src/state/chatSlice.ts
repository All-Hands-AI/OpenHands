import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type SliceState = { messages: (Message)[] };

const initialState: SliceState = {
  messages: [],
};

export const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addUserMessage(
      state,
      action: PayloadAction<{
        content: string;
        imageUrls: string[];
        timestamp: string;
      }>,
    ) {
      const message: Message = {
        sender: "user",
        content: action.payload.content,
        imageUrls: action.payload.imageUrls,
        timestamp: action.payload.timestamp || new Date().toISOString(),
      };
      state.messages.push(message);
    },

    addAssistantMessage(state, action: PayloadAction<string>) {
      const message: Message = {
        sender: "assistant",
        content: action.payload,
        imageUrls: [],
        timestamp: new Date().toISOString(),
      };
      state.messages.push(message);
    },

    addAssistantAction(state, action: PayloadAction<object>) {
      const actionID = action.payload.action;
      const messageID = `ACTION_MESSAGE\$${actionID.toUpperCase()}`;
      let text = "";
      console.log('action', action.payload);
      if (actionID === "run") {
        text = `\`${action.payload.args.command}\``;
      } else if (actionID === "run_ipython") {
        text = `\`\`\`\n${action.payload.args.code}\n\`\`\``;
      } else if (actionID === "write") {
        text = `${action.payload.args.path}\n${action.payload.args.content}`;
      } else if (actionID === "read") {
        text = action.payload.args.path;
      } else {
        return;
      }
      const message: Message = {
        type: "action",
        sender: "assistant",
        id: messageID,
        content: text,
        imageUrls: [],
        timestamp: new Date().toISOString(),
      };
      state.messages.push(message);
    },

    addErrorMessage(
      state,
      action: PayloadAction<{ id?: string; message: string }>,
    ) {
      const { id, message } = action.payload;
      state.messages.push({ id, message, type: "error" });
    },

    clearMessages(state) {
      state.messages = [];
    },
  },
});

export const {
  addUserMessage,
  addAssistantMessage,
  addAssistantAction,
  addErrorMessage,
  clearMessages,
} = chatSlice.actions;
export default chatSlice.reducer;
