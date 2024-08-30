import { Tooltip } from "@nextui-org/react";
import React, { useEffect } from "react";
import ArrowIcon from "#/assets/arrow";
import PauseIcon from "#/assets/pause";
import PlayIcon from "#/assets/play";
import { useSession } from "#/context/session";

type IgnoreTaskStateMapKeys = Extract<
  AgentState,
  | "paused"
  | "running"
  | "stopped"
  | "user_confirmed"
  | "user_rejected"
  | "awaiting_user_confirmation"
>;

const IgnoreTaskStateMap: Record<IgnoreTaskStateMapKeys, AgentState[]> = {
  paused: [
    "init",
    "paused",
    "stopped",
    "finished",
    "rejected",
    "awaiting_user_input",
    "awaiting_user_confirmation",
  ],
  running: [
    "init",
    "running",
    "stopped",
    "finished",
    "rejected",
    "awaiting_user_input",
    "awaiting_user_confirmation",
  ],
  stopped: ["init", "stopped"],
  user_confirmed: ["running"],
  user_rejected: ["running"],
  awaiting_user_confirmation: [],
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
  large = false,
}: React.PropsWithChildren<ButtonProps>): React.ReactNode {
  return (
    <Tooltip content={content} closeDelay={100}>
      <button
        onClick={() => handleAction(action)}
        disabled={isDisabled}
        className={`
          relative overflow-visible cursor-default hover:cursor-pointer group
          disabled:cursor-not-allowed disabled:opacity-60
          ${large ? "rounded-full bg-neutral-800 p-3" : ""}
          transition-all duration-300 ease-in-out
        `}
        type="button"
      >
        <span className="relative z-10 group-hover:filter group-hover:drop-shadow-[0_0_5px_rgba(255,64,0,0.4)]">
          {children}
        </span>
        <span className="absolute -inset-[5px] border-2 border-red-400/40 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 ease-in-out" />
      </button>
    </Tooltip>
  );
}

function AgentControlBar() {
  const { data, triggerAgentStateChange, clearEventLog } = useSession();
  const [desiredState, setDesiredState] = React.useState<AgentState>("init");
  const [isLoading, setIsLoading] = React.useState(false);

  const handleAction = (action: AgentState) => {
    if (
      action in Object.keys(IgnoreTaskStateMap) &&
      IgnoreTaskStateMap[action as keyof typeof IgnoreTaskStateMap].includes(
        data.agentState,
      )
    ) {
      return;
    }

    if (action === "stopped") {
      clearEventLog();
    } else {
      setIsLoading(true);
    }

    setDesiredState(action);
    triggerAgentStateChange(action);
  };

  useEffect(() => {
    if (data.agentState === desiredState) {
      if (data.agentState === "stopped") {
        clearEventLog();
      }
      setIsLoading(false);
    } else if (data.agentState === "running") {
      setDesiredState("running");
    }
  }, [data.agentState]);

  return (
    <div className="flex justify-between items-center gap-20">
      <div className="flex items-center gap-3">
        {data.agentState === "paused" ? (
          <ActionButton
            isDisabled={
              isLoading || IgnoreTaskStateMap.running.includes(data.agentState)
            }
            content="Resume the agent task"
            action="running"
            handleAction={handleAction}
            large
          >
            <PlayIcon />
          </ActionButton>
        ) : (
          <ActionButton
            isDisabled={
              isLoading || IgnoreTaskStateMap.paused.includes(data.agentState)
            }
            content="Pause the current task"
            action="paused"
            handleAction={handleAction}
            large
          >
            <PauseIcon />
          </ActionButton>
        )}
        <ActionButton
          isDisabled={isLoading}
          content="Start a new task"
          action="stopped"
          handleAction={handleAction}
        >
          <ArrowIcon />
        </ActionButton>
      </div>
    </div>
  );
}

export default AgentControlBar;
