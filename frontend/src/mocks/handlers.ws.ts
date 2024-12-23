import { delay, WebSocketHandler, ws } from "msw";
import { toSocketIo } from "@mswjs/socket.io-binding";
import { AgentState } from "#/types/agent-state";
import { InitConfig } from "#/types/core/variances";
import { SESSION_HISTORY } from "./session-history.mock";
import {
  generateAgentStateChangeObservation,
  emitMessages,
  emitAssistantMessage,
} from "./mock-ws-helpers";

const isInitConfig = (data: unknown): data is InitConfig =>
  typeof data === "object" &&
  data !== null &&
  "action" in data &&
  data.action === "initialize";

const chat = ws.link(`ws://${window?.location.host}/socket.io`);

export const handlers: WebSocketHandler[] = [
  chat.addEventListener("connection", (connection) => {
    const io = toSocketIo(connection);

    io.client.on("oh_action", async (_, data) => {
      if (isInitConfig(data)) {
        io.client.emit(
          "oh_event",
          generateAgentStateChangeObservation(AgentState.INIT),
        );

        if (data.token) {
          emitMessages(io, SESSION_HISTORY[data.token]);

          io.client.emit(
            "oh_event",
            generateAgentStateChangeObservation(AgentState.AWAITING_USER_INPUT),
          );
        }
      } else {
        io.client.emit(
          "oh_event",
          generateAgentStateChangeObservation(AgentState.RUNNING),
        );

        await delay(2500);
        emitAssistantMessage(io, "Hello!");

        io.client.emit(
          "oh_event",
          generateAgentStateChangeObservation(AgentState.AWAITING_USER_INPUT),
        );
      }
    });
  }),
];
