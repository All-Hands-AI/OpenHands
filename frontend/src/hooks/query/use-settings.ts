import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { DEFAULT_SETTINGS } from "#/services/settings";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "#/hooks/query/use-config";

const getSettingsQueryFn = async () => {
  const apiSettings = await OpenHands.getSettings();

  return {
    LLM_MODEL: apiSettings.llm_model,
    LLM_BASE_URL: apiSettings.llm_base_url,
    AGENT: apiSettings.agent,
    LANGUAGE: apiSettings.language,
    CONFIRMATION_MODE: apiSettings.confirmation_mode,
    SECURITY_ANALYZER: apiSettings.security_analyzer,
    LLM_API_KEY: apiSettings.llm_api_key,
    REMOTE_RUNTIME_RESOURCE_FACTOR: apiSettings.remote_runtime_resource_factor,
    GITHUB_TOKEN_IS_SET: apiSettings.github_token_is_set,
    ENABLE_DEFAULT_CONDENSER: apiSettings.enable_default_condenser,
    USER_CONSENTS_TO_ANALYTICS: apiSettings.user_consents_to_analytics,
  };
};

export const useSettings = () => {
  const { setGitHubTokenIsSet, githubTokenIsSet } = useAuth();
  const { data: config } = useConfig();

  const query = useQuery({
    queryKey: ["settings"],
    queryFn: getSettingsQueryFn,
    initialData: DEFAULT_SETTINGS,
    staleTime: 0,
    retry: false,
    enabled: config?.APP_MODE !== "saas" || githubTokenIsSet,
    meta: {
      disableToast: true,
    },
  });

  React.useEffect(() => {
    if (query.data?.LLM_API_KEY) {
      posthog.capture("user_activated");
    }
  }, [query.data?.LLM_API_KEY]);

  React.useEffect(() => {
    setGitHubTokenIsSet(!!query.data?.GITHUB_TOKEN_IS_SET);
  }, [query.data?.GITHUB_TOKEN_IS_SET, query.isFetched]);

  // Return default settings if in SAAS mode and not authenticated
  if (config?.APP_MODE === "saas" && !githubTokenIsSet) {
    return {
      ...query,
      data: DEFAULT_SETTINGS,
    };
  }

  return query;
};
