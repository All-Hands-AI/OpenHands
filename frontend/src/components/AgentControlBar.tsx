import React, { useEffect } from "react";
import { Button, ButtonGroup, Tooltip } from "@nextui-org/react";
import { useSelector } from "react-redux";
import PauseIcon from "../assets/pause";
import PlayIcon from "../assets/play";
import AgentTaskAction from "../types/AgentTaskAction";
import { changeTaskState } from "../services/agentStateService";
import store, { RootState } from "../store";
import AgentTaskState from "../types/AgentTaskState";
import ArrowIcon from "../assets/arrow";
import { clearMsgs } from "../services/session";
import { clearMessages } from "../state/chatSlice";

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
  }, [curTaskState]);

  return (
    <div className="ml-5 mt-3">
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
    </div>
  );
}

export default AgentControlBar;
