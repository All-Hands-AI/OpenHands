import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import AgentTaskState from "#/types/AgentTaskState";

const AgentStatusMap: { [k: string]: { message: string; indicator: string } } =
  {
    [AgentTaskState.INIT]: {
      message: "Agent is initialized, waiting for task...",
      indicator: "bg-blue-500",
    },
    [AgentTaskState.RUNNING]: {
      message: "Agent is running task...",
      indicator: "bg-green-500",
    },
    [AgentTaskState.PAUSED]: {
      message: "Agent has paused.",
      indicator: "bg-yellow-500",
    },
    [AgentTaskState.STOPPED]: {
      message: "Agent has stopped.",
      indicator: "bg-red-500",
    },
    [AgentTaskState.FINISHED]: {
      message: "Agent has finished the task.",
      indicator: "bg-green-500",
    },
  };

function AgentStatusBar() {
  const { t } = useTranslation();
  const { initialized } = useSelector((state: RootState) => state.task);
  const { curTaskState } = useSelector((state: RootState) => state.agent);

  // TODO: Extend the agent status, e.g.:
  // - Agent is typing
  // - Agent is initializing
  // - Agent is thinking
  // - Agent is ready
  // - Agent is not available
  return (
    <div className="flex items-center">
      {initialized ? (
        <>
          <div
            className={`w-3 h-3 mr-2 rounded-full animate-pulse ${AgentStatusMap[curTaskState].indicator}`}
          />
          <span className="text-sm text-stone-400">
            {AgentStatusMap[curTaskState].message}
          </span>
        </>
      ) : (
        <>
          <div className="w-3 h-3 mr-3 bg-orange-800 rounded-full animate-pulse" />
          <span className="text-sm text-stone-400">
            {t(I18nKey.CHAT_INTERFACE$INITIALZING_AGENT_LOADING_MESSAGE)}
          </span>
        </>
      )}
    </div>
  );
}

export default AgentStatusBar;
