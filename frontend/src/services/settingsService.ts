import { appendAssistantMessage } from "../state/chatSlice";
import { setInitialized } from "../state/taskSlice";
import store from "../store";

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
export function sendSettings(
  socket: WebSocket,
  reduxSettings: { [id: string]: string },
  appendMessages: boolean = true,
): void {
  const socketSettings = Object.fromEntries(
    Object.entries(reduxSettings).map(([setting, value]) => [
      SETTINGS_MAP.get(setting) || setting,
      value,
    ]),
  );
  const event = { action: "initialize", args: socketSettings };
  const eventString = JSON.stringify(event);
  socket.send(eventString);
  store.dispatch(setInitialized(false));
  if (appendMessages) {
    for (const [setting, value] of Object.entries(reduxSettings)) {
      store.dispatch(appendAssistantMessage(`Set ${setting} to "${value}"`));
    }
  }
}
