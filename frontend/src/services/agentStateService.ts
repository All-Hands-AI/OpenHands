import ActionType from "src/types/ActionType";
import AgentTaskAction from "src/types/AgentTaskAction";
import Socket from "./socket";

export function changeTaskState(message: AgentTaskAction): void {
  const eventString = JSON.stringify({
    action: ActionType.CHANGE_TASK_STATE,
    args: { task_state_action: message },
  });
  Socket.send(eventString);
}
