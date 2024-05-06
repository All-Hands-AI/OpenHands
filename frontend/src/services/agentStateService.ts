import ActionType from "#/types/ActionType";
import AgentState from "#/types/AgentState";
import Socket from "./socket";
import { initializeAgent } from "./agent";

const INIT_DELAY = 1000;

export function changeAgentState(state: AgentState): void {
  const eventString = JSON.stringify({
    action: ActionType.CHANGE_AGENT_STATE,
    args: { agent_state: state },
  });
  Socket.send(eventString);
  if (state === AgentState.STOPPED) {
    setTimeout(() => {
      initializeAgent();
    }, INIT_DELAY);
  }
}
