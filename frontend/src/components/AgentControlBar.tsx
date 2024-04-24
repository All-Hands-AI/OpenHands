import { Tooltip } from "@nextui-org/react";
import React, { useEffect } from "react";
import { useSelector } from "react-redux";
import ArrowIcon from "#/assets/arrow";
import PauseIcon from "#/assets/pause";
import PlayIcon from "#/assets/play";
import { changeTaskState } from "#/services/agentStateService";
import { clearMsgs } from "#/services/session";
import { clearMessages } from "#/state/chatSlice";
import store, { RootState } from "#/store";
import AgentTaskAction from "#/types/AgentTaskAction";
import AgentTaskState from "#/types/AgentTaskState";

const TaskStateActionMap = {
  [AgentTaskAction.START]: AgentTaskState.RUNNING,
  [AgentTaskAction.PAUSE]: AgentTaskState.PAUSED,
  [AgentTaskAction.RESUME]: AgentTaskState.RUNNING,
  [AgentTaskAction.STOP]: AgentTaskState.STOPPED,
};

const IgnoreTaskStateMap: { [k: string]: AgentTaskState[] } = {
  [AgentTaskAction.PAUSE]: [
    AgentTaskState.INIT,
    AgentTaskState.PAUSED,
    AgentTaskState.STOPPED,
    AgentTaskState.FINISHED,
  ],
  [AgentTaskAction.RESUME]: [
    AgentTaskState.INIT,
    AgentTaskState.RUNNING,
    AgentTaskState.STOPPED,
    AgentTaskState.FINISHED,
  ],
  [AgentTaskAction.STOP]: [
    AgentTaskState.INIT,
    AgentTaskState.STOPPED,
    AgentTaskState.FINISHED,
  ],
};

interface ButtonProps {
  isDisabled: boolean;
  content: string;
  action: AgentTaskAction;
  handleAction: (action: AgentTaskAction) => void;
  large?: boolean;
}

function ActionButton({
  isDisabled = false,
  content,
  action,
  handleAction,
  children,
  large,
}: React.PropsWithChildren<ButtonProps>): React.ReactNode {
  return (
    <Tooltip content={content} closeDelay={100}>
      <button
        onClick={() => handleAction(action)}
        disabled={isDisabled}
        className={`${large ? "rounded-full bg-neutral-800 p-3" : ""} hover:opacity-80 transition-all`}
        type="button"
      >
        {children}
      </button>
    </Tooltip>
  );
}

ActionButton.defaultProps = {
  large: false,
};

function AgentControlBar() {
  const { curTaskState } = useSelector((state: RootState) => state.agent);
  const [desiredState, setDesiredState] = React.useState(AgentTaskState.INIT);
  const [isLoading, setIsLoading] = React.useState(false);

  const handleAction = (action: AgentTaskAction) => {
    if (IgnoreTaskStateMap[action].includes(curTaskState)) {
      return;
    }

    let act = action;

    if (act === AgentTaskAction.STOP) {
      act = AgentTaskAction.STOP;
      clearMsgs().then().catch();
      store.dispatch(clearMessages());
    } else {
      setIsLoading(true);
    }

    setDesiredState(TaskStateActionMap[act]);
    changeTaskState(act);
  };

  useEffect(() => {
    if (curTaskState === desiredState) {
      if (curTaskState === AgentTaskState.STOPPED) {
        clearMsgs().then().catch();
        store.dispatch(clearMessages());
      }
      setIsLoading(false);
    } else if (curTaskState === AgentTaskState.RUNNING) {
      setDesiredState(AgentTaskState.RUNNING);
    }
    // We only want to run this effect when curTaskState changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [curTaskState]);

  return (
    <div className="flex items-center gap-3">
      {curTaskState === AgentTaskState.PAUSED ? (
        <ActionButton
          isDisabled={
            isLoading ||
            IgnoreTaskStateMap[AgentTaskAction.RESUME].includes(curTaskState)
          }
          content="Resume the agent task"
          action={AgentTaskAction.RESUME}
          handleAction={handleAction}
          large
        >
          <PlayIcon />
        </ActionButton>
      ) : (
        <ActionButton
          isDisabled={
            isLoading ||
            IgnoreTaskStateMap[AgentTaskAction.PAUSE].includes(curTaskState)
          }
          content="Pause the agent task"
          action={AgentTaskAction.PAUSE}
          handleAction={handleAction}
          large
        >
          <PauseIcon />
        </ActionButton>
      )}
      <ActionButton
        isDisabled={isLoading}
        content="Restart a new agent task"
        action={AgentTaskAction.STOP}
        handleAction={handleAction}
      >
        <ArrowIcon />
      </ActionButton>
    </div>
  );
}

export default AgentControlBar;
