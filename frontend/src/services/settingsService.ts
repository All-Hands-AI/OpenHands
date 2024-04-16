import { setInitialized } from "../state/taskSlice";
import store from "../store";
import ActionType from "../types/ActionType";
import Socket from "./socket";
import { setAllSettings, setByKey } from "../state/settingsSlice";
import { ArgConfigType } from "../types/ConfigType";
import toast from "../utils/toast";

export async function fetchModels() {
  const response = await fetch(`/api/litellm-models`);
  return response.json();
}

export async function fetchAgents() {
  const response = await fetch(`/api/litellm-agents`);
  return response.json();
}

// all available settings in the frontend
// TODO: add the values to i18n to support multi languages
const DISPLAY_MAP = new Map<string, string>([
  [ArgConfigType.LLM_MODEL, "model"],
  [ArgConfigType.AGENT, "agent"],
  [ArgConfigType.WORKSPACE_DIR, "directory"],
  [ArgConfigType.LANGUAGE, "language"],
]);

type SettingsUpdateInfo = {
  mergedSettings: Record<string, string>;
  updatedSettings: Record<string, string>;
  needToSend: boolean;
};

export const getSettingsForInitialize = () => ({
    LLM_MODEL: localStorage.getItem("LLM_MODEL") || undefined,
    AGENT: localStorage.getItem("AGENT") || undefined,
});

// Function to merge and update settings
export const mergeAndUpdateSettings = (
  newSettings: Record<string, string>,
  oldSettings: Record<string, string>,
  isInit: boolean,
) =>
  Object.keys(newSettings).reduce(
    (acc, key) => {
      const newValue = String(newSettings[key]);
      const oldValue = oldSettings[key];

      // key doesn't exist in frontend settings will be overwritten by backend settings
      if (oldValue === undefined) {
        acc.mergedSettings[key] = newValue;
        acc.updatedSettings[key] = newValue;
        return acc;
      }

      if (!DISPLAY_MAP.has(key)) {
        acc.mergedSettings[key] = newValue;
        return acc;
      }

      if (oldValue === newValue || (isInit && oldValue !== "")) {
        acc.mergedSettings[key] = oldValue;
        return acc;
      }

      acc.mergedSettings[key] = newValue;
      acc.updatedSettings[key] = newValue;
      acc.needToSend = true;

      return acc;
    },
    {
      mergedSettings: { ...oldSettings },
      updatedSettings: {},
      needToSend: false,
    } as SettingsUpdateInfo,
  );

const dispatchSettings = (updatedSettings: Record<string, string>) => {
  let i = 0;
  for (const [key, value] of Object.entries(updatedSettings)) {
    if (DISPLAY_MAP.has(key)) {
      store.dispatch(setByKey({ key, value }));
      setTimeout(() => {
        toast.settingsChanged(`Set ${DISPLAY_MAP.get(key)} to "${value}"`);
      }, i * 500);
      i += 1;
    }
  }
};

const sendSettings = (
  mergedSettings: Record<string, string>,
  needToSend: boolean,
  isInit: boolean,
) => {
  const settingsCopy = { ...mergedSettings };
  delete settingsCopy.ALL_SETTINGS;

  if (needToSend || isInit) {
    const event = { action: ActionType.INIT, args: settingsCopy };
    const eventString = JSON.stringify(event);
    store.dispatch(setInitialized(false));
    Socket.send(eventString);
  }
};

// Save and send settings to the server
export function saveSettings(
  newSettings: { [key: string]: string },
  oldSettings: { [key: string]: string },
  isInit: boolean = false,
): void {
  const { mergedSettings, updatedSettings, needToSend } =
    mergeAndUpdateSettings(newSettings, oldSettings, isInit);

  dispatchSettings(updatedSettings);

  if (isInit) {
    store.dispatch(setAllSettings(JSON.stringify(newSettings)));
  }

  sendSettings(mergedSettings, needToSend, isInit);
}
