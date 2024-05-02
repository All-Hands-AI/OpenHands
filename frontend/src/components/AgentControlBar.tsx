import { Tooltip } from "@nextui-org/react";
import React, { useEffect } from "react";
import { useSelector } from "react-redux";
import ArrowIcon from "#/assets/arrow";
import PauseIcon from "#/assets/pause";
import PlayIcon from "#/assets/play";
import { changeAgentState } from "#/services/agentStateService";
import { clearMsgs } from "#/services/session";
import { clearMessages } from "#/state/chatSlice";
import store, { RootState } from "#/store";
import AgentState from "#/types/AgentState";

const TaskStateActionMap = {
  [AgentState.RUNNING]: AgentState.RUNNING,
  [AgentState.PAUSED]: AgentState.PAUSED,
  [AgentState.RUNNING]: AgentState.RUNNING,
  [AgentState.STOPPED]: AgentState.STOPPED,
};

const IgnoreTaskStateMap: { [k: string]: AgentState[] } = {
  [AgentState.PAUSED]: [
    AgentState.INIT,
    AgentState.PAUSED,
    AgentState.STOPPED,
    AgentState.FINISHED,
    AgentState.AWAITING_USER_INPUT,
  ],
  [AgentState.RUNNING]: [
    AgentState.INIT,
    AgentState.RUNNING,
    AgentState.STOPPED,
    AgentState.FINISHED,
    AgentState.AWAITING_USER_INPUT,
  ],
  [AgentState.STOPPED]: [
    AgentState.INIT,
    AgentState.STOPPED,
    AgentState.FINISHED,
  ],
};

interface ButtonProps {
  isDisabled: boolean;
  content: string;
  action: AgentState;
  handleAction: (action: AgentState) => void;
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
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const [desiredState, setDesiredState] = React.useState(AgentState.INIT);
  const [isLoading, setIsLoading] = React.useState(false);

  const handleAction = (action: AgentState) => {
    if (IgnoreTaskStateMap[action].includes(curAgentState)) {
      return;
    }

    let act = action;

    if (act === AgentState.STOPPED) {
      act = AgentState.STOPPED;
      clearMsgs().then().catch();
      store.dispatch(clearMessages());
    } else {
      setIsLoading(true);
    }

    setDesiredState(TaskStateActionMap[act]);
    changeAgentState(act);
  };

  useEffect(() => {
    if (curAgentState === desiredState) {
      if (curAgentState === AgentState.STOPPED) {
        clearMsgs().then().catch();
        store.dispatch(clearMessages());
      }
      setIsLoading(false);
    } else if (curAgentState === AgentState.RUNNING) {
      setDesiredState(AgentState.RUNNING);
    }
    // We only want to run this effect when curAgentState changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [curAgentState]);

  return (
    <div className="flex items-center gap-3">
      {curAgentState === AgentState.PAUSED ? (
        <ActionButton
          isDisabled={
            isLoading ||
            IgnoreTaskStateMap[AgentState.RUNNING].includes(curAgentState)
          }
          content="Resume the agent task"
          action={AgentState.RUNNING}
          handleAction={handleAction}
          large
        >
          <PlayIcon />
        </ActionButton>
      ) : (
        <ActionButton
          isDisabled={
            isLoading ||
            IgnoreTaskStateMap[AgentState.PAUSED].includes(curAgentState)
          }
          content="Pause the agent task"
          action={AgentState.PAUSED}
          handleAction={handleAction}
          large
        >
          <PauseIcon />
        </ActionButton>
      )}
      <ActionButton
        isDisabled={isLoading}
        content="Restart a new agent task"
        action={AgentState.STOPPED}
        handleAction={handleAction}
      >
        <ArrowIcon />
      </ActionButton>
    </div>
  );
}

export default AgentControlBar;
