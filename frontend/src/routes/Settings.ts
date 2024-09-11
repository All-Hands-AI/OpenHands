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
  console.log(Object.fromEntries(formData.entries()));

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
  return json(null);
};
