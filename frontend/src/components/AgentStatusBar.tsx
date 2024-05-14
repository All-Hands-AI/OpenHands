import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";

const AgentStatusMap: { [k: string]: { message: string; indicator: string } } =
  {
    [AgentState.INIT]: {
      message: "Agent is initialized, waiting for task...",
      indicator: "bg-blue-500",
    },
    [AgentState.RUNNING]: {
      message: "Agent is running task...",
      indicator: "bg-green-500",
    },
    [AgentState.AWAITING_USER_INPUT]: {
      message: "Agent is awaiting user input...",
      indicator: "bg-orange-500",
    },
    [AgentState.PAUSED]: {
      message: "Agent has paused.",
      indicator: "bg-yellow-500",
    },
    [AgentState.LOADING]: {
      message: "Agent is initializing...",
      indicator: "bg-yellow-500",
    },
    [AgentState.STOPPED]: {
      message: "Agent has stopped.",
      indicator: "bg-red-500",
    },
    [AgentState.FINISHED]: {
      message: "Agent has finished the task.",
      indicator: "bg-green-500",
    },
    [AgentState.ERROR]: {
      message: "Agent encountered an error.",
      indicator: "bg-red-500",
    },
  };

function AgentStatusBar() {
  const { t } = useTranslation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  // TODO: Extend the agent status, e.g.:
  // - Agent is typing
  // - Agent is initializing
  // - Agent is thinking
  // - Agent is ready
  // - Agent is not available
  return (
    <div className="flex items-center">
      {curAgentState !== AgentState.LOADING ? (
        <>
          <div
            className={`w-3 h-3 mr-2 rounded-full animate-pulse ${AgentStatusMap[curAgentState].indicator}`}
          />
          <span className="text-sm text-stone-400">
            {AgentStatusMap[curAgentState].message}
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
