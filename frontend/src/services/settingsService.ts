import { setInitialized } from "../state/taskSlice";
import store from "../store";
import ActionType from "../types/ActionType";
import { SupportedSettings, ArgConfigType } from "../types/ConfigType";
import Socket from "./socket";
import { setByKey } from "../state/settingsSlice";
import toast from "../utils/toast";

export async function fetchModels() {
  const response = await fetch(`/api/litellm-models`);
  return response.json();
}

export async function fetchAgents() {
  const response = await fetch(`/api/agents`);
  return response.json();
}

// all available settings in the frontend
// TODO: add the values to i18n to support multi languages
const DISPLAY_MAP = new Map<string, string>([
  [ArgConfigType.LLM_MODEL, "model"],
  [ArgConfigType.AGENT, "agent"],
  [ArgConfigType.LANGUAGE, "language"],
]);

const DEFAULT_SETTINGS = new Map<string, string>([
  [ArgConfigType.LLM_MODEL, "gpt-3.5-turbo"],
  [ArgConfigType.AGENT, "MonologueAgent"],
  [ArgConfigType.LANGUAGE, "en"],
]);

const getSettingOrDefault = (key: string) => {
  const value = localStorage.getItem(key);
  return value || DEFAULT_SETTINGS.get(key);
}

export const getCurrentSettings = () => ({
    LLM_MODEL: getSettingOrDefault("LLM_MODEL"),
    AGENT: getSettingOrDefault("AGENT"),
    LANGUAGE: getSettingOrDefault("LANGUAGE"),
});

// Function to merge and update settings
export const getUpdatedSettings = (newSettings: map<string, string>) => {
  const currentSettings = getCurrentSettings();
  const updatedSettings = {};
  SupportedSettings.forEach((setting) => {
    if (newSettings[setting] !== currentSettings[setting]) {
      updatedSettings[setting] = newSettings[setting];
    }
  });
  return updatedSettings;
};

const dispatchSettings = (updatedSettings: Record<string, string>) => {
  let i = 0;
  for (const [key, value] of Object.entries(updatedSettings)) {
    store.dispatch(setByKey({ key, value }));
    if (DISPLAY_MAP.has(key)) {
      setTimeout(() => {
        toast.settingsChanged(`Set ${DISPLAY_MAP.get(key)} to "${value}"`);
      }, i * 500);
      i += 1;
    }
  }
};

const initializeAgent = () => {
  const event = { action: ActionType.INIT, args: getCurrentSettings() };
  const eventString = JSON.stringify(event);
  store.dispatch(setInitialized(false));
  Socket.send(eventString);
};

// Save and send settings to the server
export function saveSettings(newSettings: { [key: string]: string }): void {
  const updatedSettings = getUpdatedSettings(newSettings);

  if (Object.keys(updatedSettings).length === 0) {
    return;
  }

  dispatchSettings(updatedSettings);
  initializeAgent();
}
