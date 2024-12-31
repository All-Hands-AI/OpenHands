import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { AxiosError } from "axios";
import { DEFAULT_SETTINGS, getLocalStorageSettings } from "#/services/settings";
import OpenHands from "#/api/open-hands";

const getSettingsQueryFn = async () => {
  try {
    const apiSettings = await OpenHands.getSettings();

    if (apiSettings !== null) {
      return {
        LLM_MODEL: apiSettings.llm_model,
        LLM_BASE_URL: apiSettings.llm_base_url,
        AGENT: apiSettings.agent,
        LANGUAGE: apiSettings.language,
        CONFIRMATION_MODE: apiSettings.confirmation_mode,
        SECURITY_ANALYZER: apiSettings.security_analyzer,
        LLM_API_KEY: apiSettings.llm_api_key,
      };
    }

    return getLocalStorageSettings();
  } catch (error) {
    if (error instanceof AxiosError) {
      if (error.response?.status === 404) {
        return DEFAULT_SETTINGS;
      }
    }

    throw error;
  }
};

export const useSettings = () => {
  const query = useQuery({
    queryKey: ["settings"],
    queryFn: getSettingsQueryFn,
    initialData: DEFAULT_SETTINGS,
  });

  React.useEffect(() => {
    if (query.data?.LLM_API_KEY) {
      posthog.capture("user_activated");
    }
  }, [query.data?.LLM_API_KEY]);

  return query;
};
