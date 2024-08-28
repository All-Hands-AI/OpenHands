import { getSettings } from "#/services/settings";
import ActionType from "#/types/ActionType";

export const generateAgentInitEvent = () => {
  const settings = getSettings();
  const rawEvent = {
    action: ActionType.INIT,
    args: {
      ...settings,
      LLM_MODEL: settings.USING_CUSTOM_MODEL
        ? settings.CUSTOM_LLM_MODEL
        : settings.LLM_MODEL,
    },
  };
  return JSON.stringify(rawEvent);
};
