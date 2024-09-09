import { delay, WebSocketHandler, ws } from "msw";
import AgentState from "#/types/AgentState";
import {
  AgentStateChangeObservation,
  CommandObservation,
} from "#/types/core/observations";
import { AssistantMessageAction } from "#/types/core/actions";
import { TokenConfigSuccess } from "#/types/core/variances";

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

const generateAgentRunObservation = (): CommandObservation => ({
  id: 3,
  cause: 0,
  message: "COMMAND_OBSERVATION",
  source: "agent",
  timestamp: new Date().toISOString(),
  observation: "run",
  content: "COMMAND_OBSERVATION",
  extras: {
    command: "<input>",
    command_id: 1,
    exit_code: 0,
  },
});

const api = ws.link("ws://localhost:3001/ws");

export const handlers: WebSocketHandler[] = [
  api.on("connection", ({ server, client }) => {
    client.send(
      JSON.stringify({
        status: "ok",
        token: "1234",
      } satisfies TokenConfigSuccess),
    );

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
          case "run":
            await delay(2500);
            // send command observation
            client.send(
              JSON.stringify(generateAgentRunObservation(parsed.args.command)),
            );
            break;
          default:
            // send error
            break;
        }
      }
      console.warn(JSON.stringify(JSON.parse(event.data.toString()), null, 2));
    });
  }),
];
