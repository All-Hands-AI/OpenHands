import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { ActionSecurityRisk } from "#/state/security-analyzer-slice";
import {
  OpenHandsObservation,
  CommandObservation,
  IPythonObservation,
} from "#/types/core/observations";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsEventType } from "#/types/core/base";

type SliceState = { messages: Message[] };

const MAX_CONTENT_LENGTH = 1000;

const HANDLED_ACTIONS: OpenHandsEventType[] = [
  "run",
  "run_ipython",
  "write",
  "read",
  "browse",
  "edit",
];

function getRiskText(risk: ActionSecurityRisk) {
  switch (risk) {
    case ActionSecurityRisk.LOW:
      return "Low Risk";
    case ActionSecurityRisk.MEDIUM:
      return "Medium Risk";
    case ActionSecurityRisk.HIGH:
      return "High Risk";
    case ActionSecurityRisk.UNKNOWN:
    default:
      return "Unknown Risk";
  }
}

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

    addAssistantMessage(state: SliceState, action: PayloadAction<string>) {
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

    addAssistantAction(
      state: SliceState,
      action: PayloadAction<OpenHandsAction>,
    ) {
      const actionID = action.payload.action;
      if (!HANDLED_ACTIONS.includes(actionID)) {
        return;
      }
      const translationID = `ACTION_MESSAGE$${actionID.toUpperCase()}`;
      let text = "";
      if (actionID === "run") {
        text = `Command:\n\`${action.payload.args.command}\``;
      } else if (actionID === "run_ipython") {
        text = `\`\`\`\n${action.payload.args.code}\n\`\`\``;
      } else if (actionID === "write") {
        let { content } = action.payload.args;
        if (content.length > MAX_CONTENT_LENGTH) {
          content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
        }
        text = `${action.payload.args.path}\n${content}`;
      } else if (actionID === "browse") {
        text = `Browsing ${action.payload.args.url}`;
      }
      if (actionID === "run" || actionID === "run_ipython") {
        if (
          action.payload.args.confirmation_state === "awaiting_confirmation"
        ) {
          text += `\n\n${getRiskText(action.payload.args.security_risk as unknown as ActionSecurityRisk)}`;
        }
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
      state: SliceState,
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
      // Set success property based on observation type
      if (observationID === "run") {
        const commandObs = observation.payload as CommandObservation;
        causeMessage.success = commandObs.extras.metadata.exit_code === 0;
      } else if (observationID === "run_ipython") {
        // For IPython, we consider it successful if there's no error message
        const ipythonObs = observation.payload as IPythonObservation;
        causeMessage.success = !ipythonObs.content
          .toLowerCase()
          .includes("error:");
      }

      if (observationID === "run" || observationID === "run_ipython") {
        let { content } = observation.payload;
        if (content.length > MAX_CONTENT_LENGTH) {
          content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
        }
        content = `${
          causeMessage.content
        }\n\nOutput:\n\`\`\`\n${content.trim() || "[Command finished execution with no output]"}\n\`\`\``;
        causeMessage.content = content; // Observation content includes the action
      } else if (observationID === "read" || observationID === "edit") {
        const { content } = observation.payload;
        causeMessage.content = `\`\`\`${observationID === "edit" ? "diff" : "python"}\n${content}\n\`\`\``; // Content is already truncated by the ACI
      } else if (observationID === "browse") {
        let content = `**URL:** ${observation.payload.extras.url}\n`;
        if (observation.payload.extras.error) {
          content += `**Error:**\n${observation.payload.extras.error}\n`;
        }
        content += `**Output:**\n${observation.payload.content}`;
        if (content.length > MAX_CONTENT_LENGTH) {
          content = `${content.slice(0, MAX_CONTENT_LENGTH)}...`;
        }
        causeMessage.content = content;
      }
    },

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

    clearMessages(state: SliceState) {
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
