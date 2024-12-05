import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { OpenHandsObservation } from "#/types/core/observations";
import { OpenHandsAction } from "#/types/core/actions";

type SliceState = { messages: Message[] };

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
        pending?: boolean;
      }>,
    ) {
      const message: Message = {
        type: "thought",
        sender: "user",
        content: action.payload.content,
        imageUrls: action.payload.imageUrls,
        timestamp: action.payload.timestamp || new Date().toISOString(),
        pending: !!action.payload.pending,
      };
      // Remove any pending messages
      let i = state.messages.length;
      while (i) {
        i -= 1;
        const m = state.messages[i] as Message;
        if (m.pending) {
          state.messages.splice(i, 1);
        }
      }
      state.messages.push(message);
    },

    addAssistantMessage(state, action: PayloadAction<string>) {
      const message: Message = {
        type: "thought",
        sender: "assistant",
        content: action.payload,
        imageUrls: [],
        timestamp: new Date().toISOString(),
        pending: false,
      };
      state.messages.push(message);
    },

    addAssistantAction(state, action: PayloadAction<OpenHandsAction>) {
      const actionID = action.payload.action;
      if (!HANDLED_ACTIONS.includes(actionID)) {
        return;
      }
      const translationID = `ACTION_MESSAGE$${actionID.toUpperCase()}`;
      let text = "";
      if (actionID === "run") {
        text = `\`${action.payload.args.command}\``;
      } else if (actionID === "run_ipython") {
        text = `\`\`\`\n${action.payload.args.code}\n\`\`\``;
      } else if (actionID === "write") {
        let { content } = action.payload.args;
        if (content.length > MAX_CONTENT_LENGTH) {
          content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
        }
        text = `${action.payload.args.path}\n${content}`;
      } else if (actionID === "read") {
        text = action.payload.args.path;
      }
      const message: Message = {
        type: "action",
        sender: "assistant",
        translationID,
        eventID: action.payload.id,
        content: text,
        imageUrls: [],
        timestamp: new Date().toISOString(),
      };
      state.messages.push(message);
    },

    addAssistantObservation(
      state,
      observation: PayloadAction<OpenHandsObservation>,
    ) {
      const observationID = observation.payload.observation;
      if (!HANDLED_ACTIONS.includes(observationID)) {
        return;
      }
      const translationID = `OBSERVATION_MESSAGE$${observationID.toUpperCase()}`;
      const causeID = observation.payload.cause;
      const causeMessage = state.messages.find(
        (message) => message.eventID === causeID,
      );
      if (!causeMessage) {
        return;
      }
      causeMessage.translationID = translationID;
      if (observationID === "run" || observationID === "run_ipython") {
        let { content } = observation.payload;
        if (content.length > MAX_CONTENT_LENGTH) {
          content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
        }
        content = `\`\`\`\n${content}\n\`\`\``;
        causeMessage.content = content; // Observation content includes the action
      }
    },

    addErrorMessage(
      state,
      action: PayloadAction<{ id?: string; message: string }>,
    ) {
      const { id, message } = action.payload;
      console.log("add err message", id, message);
      state.messages.push({
        translationID: id,
        content: message,
        type: "error",
        sender: "assistant",
        timestamp: new Date().toISOString(),
      });
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
