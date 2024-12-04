import { WebSocketHandler, ws } from "msw";
import { toSocketIo } from "@mswjs/socket.io-binding";
import AgentState from "#/types/agent-state";

const chat = ws.link(`ws://${window?.location.host}/socket.io`);

export const handlers: WebSocketHandler[] = [
  chat.addEventListener("connection", (connection) => {
    const io = toSocketIo(connection);
    console.warn("Connected to chat");

    io.client.emit("connect");

    io.client.emit("oh_event", {
      id: 1,
      cause: 0,
      message: "AGENT_STATE_CHANGE_MESSAGE",
      source: "agent",
      timestamp: new Date().toISOString(),
      observation: "agent_state_changed",
      content: "AGENT_STATE_CHANGE_MESSAGE",
      extras: { agent_state: AgentState.INIT },
    });

    io.client.on("oh_action", () => {
      io.client.emit("oh_event", {
        id: 2,
        message: "USER_MESSAGE",
        source: "agent",
        timestamp: new Date().toISOString(),
        action: "message",
        args: {
          content: "Hello, World!",
          image_urls: [],
          wait_for_response: false,
        },
      });
    });
  }),
];
