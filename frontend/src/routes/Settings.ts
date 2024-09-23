import { ClientActionFunctionArgs, json } from "@remix-run/react";
import {
  getDefaultSettings,
  LATEST_SETTINGS_VERSION,
  saveSettings,
  Settings,
  settingsAreUpToDate,
} from "#/services/settings";

// This is the route for saving settings. It only exports the action function.
export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const intent = formData.get("intent")?.toString();

  if (intent === "account") {
    const LANGUAGE = formData.get("language")?.toString();
    if (LANGUAGE) saveSettings({ LANGUAGE });

    return json({ success: true });
  }

  if (intent === "reset") {
    saveSettings(getDefaultSettings());
    return json(null);
  }

  const isUsingCustomModel = Object.keys(
    Object.fromEntries(formData.entries()),
  ).includes("use-custom-model");

  let customModel: string | undefined;
  let baseUrl: string | undefined;

  if (isUsingCustomModel) {
    customModel = formData.get("custom-model")?.toString();
    baseUrl = formData.get("base-url")?.toString();
  }

  const provider = formData.get("llm-provider")?.toString();
  const model = formData.get("llm-model")?.toString();

  const LLM_MODEL = customModel || `${provider}/${model}`.toLowerCase();
  const LLM_API_KEY = formData.get("api-key")?.toString();
  const AGENT = formData.get("agent")?.toString();
  const LANGUAGE = formData.get("language")?.toString();
  const LLM_BASE_URL = baseUrl;

  const settings: Partial<Settings> = {
    LLM_MODEL,
    LLM_API_KEY,
    AGENT,
    LANGUAGE,
    LLM_BASE_URL,
  };

  saveSettings(settings);
  // store for settings view
  localStorage.setItem(
    "use-custom-model",
    isUsingCustomModel ? "true" : "false",
  );

  // If the settings version is different from the current version, update it.
  if (!settingsAreUpToDate) {
    localStorage.setItem(
      "SETTINGS_VERSION",
      LATEST_SETTINGS_VERSION.toString(),
    );
  }

  return json({ success: true });
};
