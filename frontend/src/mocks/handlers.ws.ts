import { delay, WebSocketHandler, ws } from "msw";
import AgentState from "#/types/agent-state";
import {
  AgentStateChangeObservation,
  CommandObservation,
} from "#/types/core/observations";
import { AssistantMessageAction } from "#/types/core/actions";
import { TokenConfigSuccess } from "#/types/core/variances";
import EventLogger from "#/utils/event-logger";

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
    image_urls: [],
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

const api = ws.link("ws://localhost:3000/socket.io/?EIO=4&transport=websocket");

export const handlers: WebSocketHandler[] = [
  api.addEventListener("connection", ({ client }) => {
    client.send(
      JSON.stringify({
        status: 200,
        token: Math.random().toString(36).substring(7),
      } satisfies TokenConfigSuccess),
    );

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
            client.send(JSON.stringify(generateAgentRunObservation()));
            break;
          case "change_agent_state":
            await delay();
            // send agent state change observation
            client.send(
              JSON.stringify(
                generateAgentStateChangeObservation(parsed.args.agent_state),
              ),
            );
            break;
          default:
            // send error
            break;
        }
      }
      EventLogger.message(event);
    });
  }),
];
