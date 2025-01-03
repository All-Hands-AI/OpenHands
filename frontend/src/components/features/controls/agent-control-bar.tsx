import { useSelector } from "react-redux";
import PauseIcon from "#/assets/pause";
import PlayIcon from "#/assets/play";
import { generateAgentStateChangeEvent } from "#/services/agent-state-service";
import { RootState } from "#/store";
import { AgentState } from "#/types/agent-state";
import { useWsClient } from "#/context/ws-client-provider";
import { IGNORE_TASK_STATE_MAP } from "#/ignore-task-state-map.constant";
import { ActionButton } from "#/components/shared/buttons/action-button";

export function AgentControlBar() {
  const { send } = useWsClient();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const handleAction = (action: AgentState) => {
    if (!IGNORE_TASK_STATE_MAP[action].includes(curAgentState)) {
      send(generateAgentStateChangeEvent(action));
    }
  };

  return (
    <div className="flex justify-between items-center gap-20">
      <ActionButton
        isDisabled={
          curAgentState !== AgentState.RUNNING &&
          curAgentState !== AgentState.PAUSED
        }
        content={
          curAgentState === AgentState.PAUSED
            ? "Resume the agent task"
            : "Pause the current task"
        }
        action={
          curAgentState === AgentState.PAUSED
            ? AgentState.RUNNING
            : AgentState.PAUSED
        }
        handleAction={handleAction}
      >
        {curAgentState === AgentState.PAUSED ? <PlayIcon /> : <PauseIcon />}
      </ActionButton>
    </div>
  );
}
