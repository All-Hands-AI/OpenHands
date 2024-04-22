import { Button, ButtonGroup, Tooltip } from "@nextui-org/react";
import React, { useEffect } from "react";
import { useSelector } from "react-redux";
import ArrowIcon from "src/assets/arrow";
import PauseIcon from "src/assets/pause";
import PlayIcon from "src/assets/play";
import { changeTaskState } from "src/services/agentStateService";
import { clearMsgs } from "src/services/session";
import { clearMessages } from "src/state/chatSlice";
import store, { RootState } from "src/store";
import AgentTaskAction from "src/types/AgentTaskAction";
import AgentTaskState from "src/types/AgentTaskState";

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
  isLoading: boolean;
  isDisabled: boolean;
  content: string;
  action: AgentTaskAction;
  handleAction: (action: AgentTaskAction) => void;
}

function ActionButton({
  isLoading = false,
  isDisabled = false,
  content,
  action,
  handleAction,
  children,
}: React.PropsWithChildren<ButtonProps>): React.ReactNode {
  return (
    <Tooltip content={content} closeDelay={100}>
      <Button
        isIconOnly
        onClick={() => handleAction(action)}
        isLoading={isLoading}
        isDisabled={isDisabled}
      >
        {children}
      </Button>
    </Tooltip>
  );
}

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
    <ButtonGroup size="sm" variant="ghost">
      <ActionButton
        isLoading={false}
        isDisabled={isLoading}
        content="Restart a new agent task"
        action={AgentTaskAction.STOP}
        handleAction={handleAction}
      >
        <ArrowIcon />
      </ActionButton>

      {curTaskState === AgentTaskState.PAUSED ? (
        <ActionButton
          isLoading={isLoading}
          isDisabled={
            isLoading ||
            IgnoreTaskStateMap[AgentTaskAction.RESUME].includes(curTaskState)
          }
          content="Resume the agent task"
          action={AgentTaskAction.RESUME}
          handleAction={handleAction}
        >
          <PlayIcon />
        </ActionButton>
      ) : (
        <ActionButton
          isLoading={isLoading}
          isDisabled={
            isLoading ||
            IgnoreTaskStateMap[AgentTaskAction.PAUSE].includes(curTaskState)
          }
          content="Pause the agent task"
          action={AgentTaskAction.PAUSE}
          handleAction={handleAction}
        >
          <PauseIcon />
        </ActionButton>
      )}
    </ButtonGroup>
  );
}

export default AgentControlBar;
