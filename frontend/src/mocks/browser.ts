import { delay, WebSocketHandler, ws } from "msw";
import { setupWorker } from "msw/browser";
import AgentState from "#/types/AgentState";
import { AgentStateChangeObservation } from "#/types/core/observations";
import { AssistantMessageAction } from "#/types/core/actions";

const generateAgentStateChangeObservation = (
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

const generateAgentResponse = (message: string): AssistantMessageAction => ({
  id: 2,
  message: "USER_MESSAGE",
  source: "agent",
  timestamp: new Date().toISOString(),
  action: "message",
  args: {
    content: message,
    images_urls: [],
    wait_for_response: false,
  },
});

const api = ws.link("ws://localhost:3001/ws");

const handlers: WebSocketHandler[] = [
  api.on("connection", ({ server, client }) => {
    // data received from the server
    server.addEventListener("message", (event) => {
      console.log("data received from server", event.data);
    });

    // data received from the client
    client.addEventListener("message", async (event) => {
      const parsed = JSON.parse(event.data.toString());
      if ("action" in parsed) {
        switch (parsed.action) {
          case "initialize":
            // agent init
            client.send(
              JSON.stringify(
                generateAgentStateChangeObservation(AgentState.INIT),
              ),
            );
            break;
          case "message":
            client.send(
              JSON.stringify(
                generateAgentStateChangeObservation(AgentState.RUNNING),
              ),
            );
            await delay(2500);
            // send message
            client.send(JSON.stringify(generateAgentResponse("Hello, World!")));
            client.send(
              JSON.stringify(
                generateAgentStateChangeObservation(
                  AgentState.AWAITING_USER_INPUT,
                ),
              ),
            );
            break;
          default:
            // send error
            break;
        }
      }
      console.warn(JSON.stringify(JSON.parse(event.data.toString()), null, 2));
    });

    console.log("Connected to the server");
  }),
];

export const worker = setupWorker(...handlers);
