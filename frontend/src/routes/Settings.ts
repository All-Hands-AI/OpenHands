import { ClientActionFunctionArgs, json } from "@remix-run/react";
import {
  getDefaultSettings,
  saveSettings,
  Settings,
} from "#/services/settings";

// This is the route for saving settings. It only exports the action function.
export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const intent = formData.get("intent")?.toString();
  const settingsVersion = localStorage.getItem("SETTINGS_VERSION");

  if (intent === "reset") {
    saveSettings(getDefaultSettings());
    return json(null);
  }

  const provider = formData.get("llm-provider")?.toString();
  const model = formData.get("llm-model")?.toString();

  const LLM_MODEL = `${provider}/${model}`.toLowerCase();
  const LLM_API_KEY = formData.get("api-key")?.toString();
  const AGENT = formData.get("agent")?.toString();
  const LANGUAGE = formData.get("language")?.toString();

  const settings: Partial<Settings> = {
    LLM_MODEL,
    LLM_API_KEY,
    AGENT,
    LANGUAGE,
  };

  saveSettings(settings);

  // If the settings version is different from the current version, update it.
  if (settingsVersion !== import.meta.env.VITE_SETTINGS_VERSION) {
    localStorage.setItem(
      "SETTINGS_VERSION",
      import.meta.env.VITE_SETTINGS_VERSION,
    );
  }

  return json(null);
};
