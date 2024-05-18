import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import AgentState from "#/types/AgentState";

enum IndicatorColor {
  BLUE = "bg-blue-500",
  GREEN = "bg-green-500",
  ORANGE = "bg-orange-500",
  YELLOW = "bg-yellow-500",
  RED = "bg-red-500",
  DARK_ORANGE = "bg-orange-800",
}

function AgentStatusBar() {
  const { t } = useTranslation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const AgentStatusMap: {
    [k: string]: { message: string; indicator: IndicatorColor };
  } = {
    [AgentState.INIT]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_INIT_MESSAGE),
      indicator: IndicatorColor.BLUE,
    },
    [AgentState.RUNNING]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_RUNNING_MESSAGE),
      indicator: IndicatorColor.GREEN,
    },
    [AgentState.AWAITING_USER_INPUT]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_AWAITING_USER_INPUT_MESSAGE),
      indicator: IndicatorColor.ORANGE,
    },
    [AgentState.PAUSED]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_PAUSED_MESSAGE),
      indicator: IndicatorColor.YELLOW,
    },
    [AgentState.LOADING]: {
      message: t(I18nKey.CHAT_INTERFACE$INITIALIZING_AGENT_LOADING_MESSAGE),
      indicator: IndicatorColor.DARK_ORANGE,
    },
    [AgentState.STOPPED]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_STOPPED_MESSAGE),
      indicator: IndicatorColor.RED,
    },
    [AgentState.FINISHED]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_FINISHED_MESSAGE),
      indicator: IndicatorColor.GREEN,
    },
    [AgentState.ERROR]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_ERROR_MESSAGE),
      indicator: IndicatorColor.RED,
    },
  };

  // TODO: Extend the agent status, e.g.:
  // - Agent is typing
  // - Agent is initializing
  // - Agent is thinking
  // - Agent is ready
  // - Agent is not available
  return (
    <div className="flex items-center">
      <div
        className={`w-3 h-3 mr-2 rounded-full animate-pulse ${AgentStatusMap[curAgentState].indicator}`}
      />
      <span className="text-sm text-stone-400">
        {AgentStatusMap[curAgentState].message}
      </span>
    </div>
  );
}

export default AgentStatusBar;
