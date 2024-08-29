import { getSettings } from "#/services/settings";
import ActionType from "#/types/ActionType";

export const generateAgentInitEvent = () => {
  const settings = getSettings();
  const event = {
    action: ActionType.INIT,
    args: {
      ...settings,
      LLM_MODEL: settings.USING_CUSTOM_MODEL
        ? settings.CUSTOM_LLM_MODEL
        : settings.LLM_MODEL,
    },
  };
  return JSON.stringify(event);
};

export const generateUserMessageEvent = (
  message: string,
  images_urls: string[],
) => {
  const event = {
    action: ActionType.MESSAGE,
    args: { content: message, images_urls },
  };
  return JSON.stringify(event);
};

export const generateUserTerminalCommandEvent = (command: string) => {
  const event = { action: ActionType.RUN, args: { command } };
  return JSON.stringify(event);
};

export const generateAgentStateChangeEvent = (agent_state: AgentState) => {
  const event = {
    action: ActionType.CHANGE_AGENT_STATE,
    args: { agent_state },
  };
  return JSON.stringify(event);
};
