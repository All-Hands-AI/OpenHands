import { ClientActionFunctionArgs, json } from "@remix-run/react";
import {
  getDefaultSettings,
  saveSettings,
  Settings,
} from "#/services/settings";

// This is the route for saving settings. It only exports the action function.

export const clientAction = async ({ request }: ClientActionFunctionArgs) => {
  const formData = await request.formData();
  const entries = Object.fromEntries(formData.entries());

  const intent = formData.get("intent")?.toString();

  if (intent === "reset") {
    saveSettings(getDefaultSettings());
    return json(null);
  }

  const USING_CUSTOM_MODEL = Object.keys(entries).includes("use-custom-model");
  const CUSTOM_LLM_MODEL = USING_CUSTOM_MODEL
    ? formData.get("custom-model")?.toString()
    : undefined;
  const LLM_MODEL = formData.get("model")?.toString();
  const LLM_API_KEY = formData.get("api-key")?.toString();
  const AGENT = formData.get("agent")?.toString();

  const settings: Partial<Settings> = {
    USING_CUSTOM_MODEL,
    CUSTOM_LLM_MODEL,
    LLM_MODEL,
    LLM_API_KEY,
    AGENT,
  };

  saveSettings(settings);
  return json(null);
};
