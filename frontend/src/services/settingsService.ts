import { setInitialized } from "../state/taskSlice";
import store from "../store";
import ActionType from "../types/ActionType";
import Socket from "./socket";
import { setAllSettings, setByKey } from "../state/settingsSlice";
import { ResConfigurations } from "../types/ResponseType";
import { ArgConfigType } from "../types/ConfigType";
import toast from "../utils/toast";

export async function fetchConfigurations(): Promise<ResConfigurations> {
  const headers = new Headers({
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });
  const response = await fetch(`/api/configurations`, { headers });
  if (response.status !== 200) {
    throw new Error("Get configurations failed.");
  }
  return (await response.json()) as ResConfigurations;
}

export async function fetchModels() {
  const response = await fetch(`/api/litellm-models`);
  return response.json();
}

export async function fetchAgents() {
  const response = await fetch(`/api/litellm-agents`);
  return response.json();
}

export const INITIAL_MODELS = [
  "gpt-3.5-turbo-1106",
  "gpt-4-0125-preview",
  "claude-3-haiku-20240307",
  "claude-3-opus-20240229",
  "claude-3-sonnet-20240229",
];

export type Model = (typeof INITIAL_MODELS)[number];

export const INITIAL_AGENTS = ["MonologueAgent", "CodeActAgent"];

export type Agent = (typeof INITIAL_AGENTS)[number];

// all available settings in the frontend
// TODO: add the values to i18n to support multi languages
const DISPLAY_MAP = new Map<string, string>([
  [ArgConfigType.LLM_MODEL, "model"],
  [ArgConfigType.AGENT, "agent"],
  [ArgConfigType.WORKSPACE_DIR, "directory"],
  [ArgConfigType.LANGUAGE, "language"],
]);

// Send settings to the server
export function saveSettings(
  newSettings: { [key: string]: string },
  oldSettings: { [key: string]: string },
  isInit: boolean = false,
): void {
  const { mergedSettings, updatedSettings, needToSend } = Object.keys(
    newSettings,
  ).reduce(
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
    } as {
      mergedSettings: { [key: string]: string };
      updatedSettings: { [key: string]: string };
      needToSend: boolean;
    },
  );

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

  if (isInit) {
    store.dispatch(setAllSettings(JSON.stringify(newSettings)));
  }

  delete mergedSettings.ALL_SETTINGS;
  if (needToSend || isInit) {
    const event = { action: ActionType.INIT, args: mergedSettings };
    const eventString = JSON.stringify(event);
    store.dispatch(setInitialized(false));
    Socket.send(eventString);
  }
}
