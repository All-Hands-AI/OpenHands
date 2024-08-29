import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import AgentState from "#/types/AgentState";
import beep from "#/utils/beep";
import { useSession } from "#/context/session";

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
  const { agentState } = useSession();

  const AgentStatusMap: Record<
    AgentState,
    { message: string; indicator: IndicatorColor }
  > = {
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
    [AgentState.REJECTED]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_REJECTED_MESSAGE),
      indicator: IndicatorColor.YELLOW,
    },
    [AgentState.ERROR]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_ERROR_MESSAGE),
      indicator: IndicatorColor.RED,
    },
    [AgentState.AWAITING_USER_CONFIRMATION]: {
      message: t(
        I18nKey.CHAT_INTERFACE$AGENT_AWAITING_USER_CONFIRMATION_MESSAGE,
      ),
      indicator: IndicatorColor.ORANGE,
    },
    [AgentState.USER_CONFIRMED]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_ACTION_USER_CONFIRMED_MESSAGE),
      indicator: IndicatorColor.GREEN,
    },
    [AgentState.USER_REJECTED]: {
      message: t(I18nKey.CHAT_INTERFACE$AGENT_ACTION_USER_REJECTED_MESSAGE),
      indicator: IndicatorColor.RED,
    },
  };

  // TODO: Extend the agent status, e.g.:
  // - Agent is typing
  // - Agent is initializing
  // - Agent is thinking
  // - Agent is ready
  // - Agent is not available
  useEffect(() => {
    if (
      agentState === AgentState.AWAITING_USER_INPUT ||
      agentState === AgentState.ERROR ||
      agentState === AgentState.INIT
    ) {
      if (document.cookie.indexOf("audio") !== -1) beep();
    }
  }, [agentState]);

  return (
    <div className="flex items-center">
      <div
        className={`w-3 h-3 mr-2 rounded-full animate-pulse ${AgentStatusMap[agentState].indicator}`}
      />
      <span className="text-sm text-stone-400">
        {AgentStatusMap[agentState].message}
      </span>
    </div>
  );
}

export default AgentStatusBar;
