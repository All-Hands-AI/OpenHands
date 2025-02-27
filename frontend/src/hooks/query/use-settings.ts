import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "#/hooks/query/use-config";
import { DEFAULT_SETTINGS } from "#/services/settings";

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
    ENABLE_SOUND_NOTIFICATIONS: apiSettings.enable_sound_notifications,
    USER_CONSENTS_TO_ANALYTICS: apiSettings.user_consents_to_analytics,
  };
};

export const useSettings = () => {
  const { setGitHubTokenIsSet, githubTokenIsSet } = useAuth();
  const { data: config } = useConfig();

  const query = useQuery({
    queryKey: ["settings", githubTokenIsSet],
    queryFn: getSettingsQueryFn,
    enabled: config?.APP_MODE !== "saas" || githubTokenIsSet,
    // Only retry if the error is not a 404 because we
    // would want to show the modal immediately if the
    // settings are not found
    retry: (_, error) => error.status !== 404,
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

  // We want to return the defaults if the settings aren't found so the user can still see the
  // options to make their initial save. We don't set the defaults in `initialData` above because
  // that would prepopulate the data to the cache and mess with expectations. Read more:
  // https://tanstack.com/query/latest/docs/framework/react/guides/initial-query-data#using-initialdata-to-prepopulate-a-query
  if (query.error?.status === 404) {
    return {
      ...query,
      data: DEFAULT_SETTINGS,
    };
  }

  return query;
};
