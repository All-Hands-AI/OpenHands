import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import type { Message } from "#/message";

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

const initialState: SliceState = {
  messages: [],
  systemMessage: null,
};

export const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
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
  },
});

export const { addAssistantObservation, addErrorMessage } = chatSlice.actions;

// Selectors
export const selectSystemMessage = (state: { chat: SliceState }) =>
  state.chat.systemMessage;

export default chatSlice.reducer;
