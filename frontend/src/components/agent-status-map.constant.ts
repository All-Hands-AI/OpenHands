import { I18nKey } from "#/i18n/declaration";
import { AgentState } from "#/types/agent-state";

enum IndicatorColor {
  BLUE = "bg-blue-500",
  GREEN = "bg-green-500",
  ORANGE = "bg-orange-500",
  YELLOW = "bg-yellow-500",
  RED = "bg-red-500",
  DARK_ORANGE = "bg-orange-800",
}

export const AGENT_STATUS_MAP: {
  [k: string]: { message: string; indicator: IndicatorColor };
} = {
  [AgentState.INIT]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_INIT_MESSAGE,
    indicator: IndicatorColor.BLUE,
  },
  [AgentState.RUNNING]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_RUNNING_MESSAGE,
    indicator: IndicatorColor.GREEN,
  },
  [AgentState.AWAITING_USER_INPUT]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_AWAITING_USER_INPUT_MESSAGE,
    indicator: IndicatorColor.ORANGE,
  },
  [AgentState.PAUSED]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_PAUSED_MESSAGE,
    indicator: IndicatorColor.YELLOW,
  },
  [AgentState.LOADING]: {
    message: I18nKey.CHAT_INTERFACE$INITIALIZING_AGENT_LOADING_MESSAGE,
    indicator: IndicatorColor.DARK_ORANGE,
  },
  [AgentState.STOPPED]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_STOPPED_MESSAGE,
    indicator: IndicatorColor.RED,
  },
  [AgentState.FINISHED]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_FINISHED_MESSAGE,
    indicator: IndicatorColor.GREEN,
  },
  [AgentState.REJECTED]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_REJECTED_MESSAGE,
    indicator: IndicatorColor.YELLOW,
  },
  [AgentState.ERROR]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_ERROR_MESSAGE,
    indicator: IndicatorColor.RED,
  },
  [AgentState.AWAITING_USER_CONFIRMATION]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_AWAITING_USER_CONFIRMATION_MESSAGE,
    indicator: IndicatorColor.ORANGE,
  },
  [AgentState.USER_CONFIRMED]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_ACTION_USER_CONFIRMED_MESSAGE,
    indicator: IndicatorColor.GREEN,
  },
  [AgentState.USER_REJECTED]: {
    message: I18nKey.CHAT_INTERFACE$AGENT_ACTION_USER_REJECTED_MESSAGE,
    indicator: IndicatorColor.RED,
  },
};
