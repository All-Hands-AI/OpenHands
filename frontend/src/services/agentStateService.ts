import ActionType from "#/types/ActionType";
import AgentTaskAction from "#/types/AgentTaskAction";
import Socket from "./socket";

export function changeAgentState(message: AgentTaskAction): void {
  const eventString = JSON.stringify({
    action: ActionType.CHANGE_AGENT_STATE,
    args: { agent_state: message },
  });
  Socket.send(eventString);
}
