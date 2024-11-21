import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type SliceState = { messages: (Message)[] };

const MAX_CONTENT_LENGTH = 1000;

const HANDLED_ACTIONS = ["run", "run_ipython", "write", "read"];

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
      if (!HANDLED_ACTIONS.includes(actionID)) {
        return;
      }
      const messageID = `ACTION_MESSAGE\$${actionID.toUpperCase()}`;
      let text = "";
      if (actionID === "run") {
        text = `\`${action.payload.args.command}\``;
      } else if (actionID === "run_ipython") {
        text = `\`\`\`\n${action.payload.args.code}\n\`\`\``;
      } else if (actionID === "write") {
        let content = action.payload.args.content;
        if (content.length > MAX_CONTENT_LENGTH) {
          content = content.slice(0, MAX_CONTENT_LENGTH) + '...';
        }
        text = `${action.payload.args.path}\n${content}`;
      } else if (actionID === "read") {
        text = action.payload.args.path;
      }
      const message: Message = {
        type: "action",
        sender: "assistant",
        id: messageID,
        eventID: action.payload.id,
        content: text,
        imageUrls: [],
        timestamp: new Date().toISOString(),
      };
      state.messages.push(message);
    },

    addAssistantObservation(state, observation: PayloadAction<object>) {
      const observationID = observation.payload.observation;
      if (!HANDLED_ACTIONS.includes(observationID)) {
        return;
      }
      const messageID = `OBSERVATION_MESSAGE\$${observationID.toUpperCase()}`;
      const causeID = observation.payload.cause;
      const causeMessage = state.messages.find(
        (message) => message.eventID === causeID,
      );
      if (!causeMessage) {
        return;
      }
      causeMessage.id = messageID;
      if (observationID === 'run' || observationID === 'run_ipython') {
        let content = observation.payload.content;
        if (content.length > MAX_CONTENT_LENGTH) {
          content = content.slice(0, MAX_CONTENT_LENGTH) + '...';
        }
        content = `\`\`\`\n${content}\n\`\`\``;
        causeMessage.content = content;  // Observation content includes the action
      }
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
  addAssistantObservation,
  addErrorMessage,
  clearMessages,
} = chatSlice.actions;
export default chatSlice.reducer;
