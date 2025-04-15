import { toSocketIo } from "@mswjs/socket.io-binding";
import { AgentState } from "#/types/agent-state";
import {
  AssistantMessageAction,
  UserMessageAction,
} from "#/types/core/actions";
import { AgentStateChangeObservation } from "#/types/core/observations";
import { MockSessionMessaage } from "./session-history.mock";

export const generateAgentStateChangeObservation = (
  state: AgentState,
): AgentStateChangeObservation => ({
  id: 1,
  cause: 0,
  message: "AGENT_STATE_CHANGE_MESSAGE",
  source: "agent",
  timestamp: new Date().toISOString(),
  observation: "agent_state_changed",
  content: "AGENT_STATE_CHANGE_MESSAGE",
  extras: { agent_state: state },
});

export const generateAssistantMessageAction = (
  message: string,
): AssistantMessageAction => ({
  id: 2,
  message: "USER_MESSAGE",
  source: "agent",
  timestamp: new Date().toISOString(),
  action: "message",
  args: {
    thought: message,
    image_urls: [],
    wait_for_response: false,
  },
});

export const generateUserMessageAction = (
  message: string,
): UserMessageAction => ({
  id: 3,
  message: "USER_MESSAGE",
  source: "user",
  timestamp: new Date().toISOString(),
  action: "message",
  args: {
    content: message,
    image_urls: [],
  },
});

export const emitAssistantMessage = (
  io: ReturnType<typeof toSocketIo>,
  message: string,
) => io.client.emit("oh_event", generateAssistantMessageAction(message));

export const emitUserMessage = (
  io: ReturnType<typeof toSocketIo>,
  message: string,
) => io.client.emit("oh_event", generateUserMessageAction(message));

export const emitMessages = (
  io: ReturnType<typeof toSocketIo>,
  messages: MockSessionMessaage[],
) => {
  messages.forEach(({ source, message }) => {
    if (source === "assistant") {
      emitAssistantMessage(io, message);
    } else {
      emitUserMessage(io, message);
    }
  });
};
