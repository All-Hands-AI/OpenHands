import { Tooltip } from "@nextui-org/react";
import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import ArrowIcon from "#/assets/arrow";
import PauseIcon from "#/assets/pause";
import PlayIcon from "#/assets/play";
import { changeTaskState } from "#/services/agentStateService";
import { clearMsgs } from "#/services/session";
import { clearMessages } from "#/state/chatSlice";
import { RootState } from "#/store";
import AgentTaskAction from "#/types/AgentTaskAction";
import AgentTaskState from "#/types/AgentTaskState";
import { initializeAgent } from "#/services/agent";
import { getSettings } from "#/services/settings";

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
    AgentTaskState.AWAITING_USER_INPUT,
  ],
  [AgentTaskAction.RESUME]: [
    AgentTaskState.INIT,
    AgentTaskState.RUNNING,
    AgentTaskState.STOPPED,
    AgentTaskState.FINISHED,
    AgentTaskState.AWAITING_USER_INPUT,
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
  isLoading?: boolean;
}

function ActionButton({
  isDisabled = false,
  content,
  action,
  handleAction,
  children,
  large,
  isLoading,
}: React.PropsWithChildren<ButtonProps>): React.ReactNode {
  return (
    <Tooltip content={content} closeDelay={100}>
      <button
        onClick={() => handleAction(action)}
        disabled={isDisabled}
        className={`${large ? "rounded-full bg-neutral-800 p-3" : ""} ${isLoading ? "animate-spin" : ""} hover:opacity-80 transition-all disabled:cursor-not-allowed`}
        type="button"
      >
        {children}
      </button>
    </Tooltip>
  );
}

ActionButton.defaultProps = {
  large: false,
  isLoading: false,
};

function AgentControlBar() {
  const dispatch = useDispatch();
  const { initialized } = useSelector((state: RootState) => state.task);
  const { curTaskState } = useSelector((state: RootState) => state.agent);
  const [desiredState, setDesiredState] = React.useState(AgentTaskState.INIT);
  const [isLoading, setIsLoading] = React.useState(false);

  const handleReset = async () => {
    if (!initialized) return;

    initializeAgent(getSettings());
    // act = AgentTaskAction.STOP;
    await clearMsgs();
    dispatch(clearMessages());
  };

  const handleAction = async (action: AgentTaskAction) => {
    if (IgnoreTaskStateMap[action].includes(curTaskState)) {
      return;
    }

    let act = action;

    if (act === AgentTaskAction.STOP) {
      act = AgentTaskAction.STOP;
      await clearMsgs();
      dispatch(clearMessages());
    } else {
      setIsLoading(true);
    }

    setDesiredState(TaskStateActionMap[act]);
    changeTaskState(act);
  };

  useEffect(() => {
    (async () => {
      if (curTaskState === desiredState) {
        if (curTaskState === AgentTaskState.STOPPED) {
          await clearMsgs();
          dispatch(clearMessages());
        }
        setIsLoading(false);
      } else if (curTaskState === AgentTaskState.RUNNING) {
        setDesiredState(AgentTaskState.RUNNING);
      }
    })();
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
        isDisabled={!initialized}
        isLoading={!initialized}
        content="Reinitialize the agent task"
        action={AgentTaskAction.STOP}
        handleAction={handleReset}
      >
        <ArrowIcon />
      </ActionButton>
    </div>
  );
}

export default AgentControlBar;
