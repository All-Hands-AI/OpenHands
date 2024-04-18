import ActionType from "../types/ActionType";
import Socket from "./socket";
import AgentTaskAction from "../types/AgentTaskAction";

export function changeTaskState(message: AgentTaskAction): void {
  const eventString = JSON.stringify({
    action: ActionType.CHANGE_TASK_STATE,
    args: { task_state_action: message },
  });
  Socket.send(eventString);
}
