import ActionType from "#/types/ActionType";
import AgentState from "#/types/AgentState";
import Socket from "./socket";

export function changeAgentState(message: AgentState): void {
  const eventString = JSON.stringify({
    action: ActionType.CHANGE_AGENT_STATE,
    args: { agent_state: message },
  });
  Socket.send(eventString);
}
