import { appendAssistantMessage } from "../state/chatSlice";
import { setInitialized } from "../state/taskSlice";
import store from "../store";
import Socket from "./socket";
import {
  setAgent,
  setLanguage,
  setModel,
  setWorkspaceDirectory,
} from "../state/settingsSlice";

export async function getInitialModel() {
  if (localStorage.getItem("model")) {
    return localStorage.getItem("model");
  }

  const res = await fetch("/api/default-model");
  return res.json();
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

// Map Redux settings to socket event arguments
const SETTINGS_MAP = new Map<string, string>([
  ["model", "model"],
  ["agent", "agent_cls"],
  ["workspaceDirectory", "directory"],
]);

// Send settings to the server
export function saveSettings(
  reduxSettings: { [id: string]: string },
  needToSend: boolean = false,
): void {
  if (needToSend) {
    const socketSettings = Object.fromEntries(
      Object.entries(reduxSettings).map(([setting, value]) => [
        SETTINGS_MAP.get(setting) || setting,
        value,
      ]),
    );
    const event = { action: "initialize", args: socketSettings };
    const eventString = JSON.stringify(event);
    store.dispatch(setInitialized(false));
    Socket.send(eventString);
  }
  for (const [setting, value] of Object.entries(reduxSettings)) {
    localStorage.setItem(setting, value);
    store.dispatch(appendAssistantMessage(`Set ${setting} to "${value}"`));
  }
  store.dispatch(setModel(reduxSettings.model));
  store.dispatch(setAgent(reduxSettings.agent));
  store.dispatch(setWorkspaceDirectory(reduxSettings.workspaceDirectory));
  store.dispatch(setLanguage(reduxSettings.language));
}
