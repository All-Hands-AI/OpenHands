import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { Message } from "#/message";

import { ActionSecurityRisk } from "#/state/security-analyzer-slice";
import { OpenHandsAction } from "#/types/core/actions";
import { OpenHandsEventType } from "#/types/core/base";
import {
  CommandObservation,
  OpenHandsObservation,
} from "#/types/core/observations";

type SliceState = {
  messages: Message[];
  systemMessage: {
    content: string;
    tools: Array<Record<string, unknown>> | null;
    openhands_version: string | null;
    agent_class: string | null;
  } | null;
};

const HANDLED_ACTIONS: OpenHandsEventType[] = [
  "run",
  "run_ipython",
  "write",
  "read",
  "browse",
  "browse_interactive",
  "edit",
  "recall",
  "think",
  "system",
  "call_tool_mcp",
  "mcp",
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
  systemMessage: null,
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
        action,
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

      // Normal handling for other observation types
      const translationID = `OBSERVATION_MESSAGE$${observationID.toUpperCase()}`;
      const causeID = observation.payload.cause;
      const causeMessage = state.messages.find(
        (message) => message.eventID === causeID,
      );
      if (!causeMessage) {
        return;
      }
      causeMessage.translationID = translationID;
      causeMessage.observation = observation;
      // Set success property based on observation type
      if (observationID === "run") {
        const commandObs = observation.payload as CommandObservation;
        // If exit_code is -1, it means the command timed out, so we set success to undefined
        // to not show any status indicator
        if (commandObs.extras.metadata.exit_code === -1) {
          causeMessage.success = undefined;
        } else {
          causeMessage.success = commandObs.extras.metadata.exit_code === 0;
        }
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
      state.systemMessage = null;
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

// Selectors
export const selectSystemMessage = (state: { chat: SliceState }) =>
  state.chat.systemMessage;

export default chatSlice.reducer;
