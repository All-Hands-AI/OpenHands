import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";
import { Settings } from "#/types/settings";

const getSettingsQueryFn = async (): Promise<Settings> => {
  const apiSettings = await OpenHands.getSettings();

  return {
    LLM_MODEL: apiSettings.llm_model,
    LLM_BASE_URL: apiSettings.llm_base_url,
    AGENT: apiSettings.agent,
    LANGUAGE: apiSettings.language,
    CONFIRMATION_MODE: apiSettings.confirmation_mode,
    SECURITY_ANALYZER: apiSettings.security_analyzer,
    LLM_API_KEY_SET: apiSettings.llm_api_key_set,
    REMOTE_RUNTIME_RESOURCE_FACTOR: apiSettings.remote_runtime_resource_factor,
    PROVIDER_TOKENS_SET: apiSettings.provider_tokens_set,
    ENABLE_DEFAULT_CONDENSER: apiSettings.enable_default_condenser,
    ENABLE_SOUND_NOTIFICATIONS: apiSettings.enable_sound_notifications,
    USER_CONSENTS_TO_ANALYTICS: apiSettings.user_consents_to_analytics,
    PROVIDER_TOKENS: apiSettings.provider_tokens,
    IS_NEW_USER: false,
  };
};

export const useSettings = () => {
  const { setProviderTokensSet, providerTokensSet, setProvidersAreSet } =
    useAuth();

  const isOnTosPage = useIsOnTosPage();

  const query = useQuery({
    queryKey: ["settings", providerTokensSet],
    queryFn: getSettingsQueryFn,
    // Only retry if the error is not a 404 because we
    // would want to show the modal immediately if the
    // settings are not found
    retry: (_, error) => error.status !== 404,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
    enabled: !isOnTosPage,
    meta: {
      disableToast: true,
    },
  });

  React.useEffect(() => {
    if (query.isFetched && query.data?.LLM_API_KEY_SET) {
      posthog.capture("user_activated");
    }
  }, [query.data?.LLM_API_KEY_SET, query.isFetched]);

  React.useEffect(() => {
    if (query.data?.PROVIDER_TOKENS_SET) {
      const providers = query.data.PROVIDER_TOKENS_SET;
      const setProviders = (
        Object.keys(providers) as Array<keyof typeof providers>
      ).filter((key) => providers[key]);
      setProviderTokensSet(setProviders);
      const atLeastOneSet = Object.values(query.data.PROVIDER_TOKENS_SET).some(
        (value) => value,
      );
      setProvidersAreSet(atLeastOneSet);
    }
  }, [query.data?.PROVIDER_TOKENS_SET, query.isFetched]);

  // We want to return the defaults if the settings aren't found so the user can still see the
  // options to make their initial save. We don't set the defaults in `initialData` above because
  // that would prepopulate the data to the cache and mess with expectations. Read more:
  // https://tanstack.com/query/latest/docs/framework/react/guides/initial-query-data#using-initialdata-to-prepopulate-a-query
  if (query.error?.status === 404) {
    // Create a new object with only the properties we need, avoiding rest destructuring
    return {
      data: DEFAULT_SETTINGS,
      error: query.error,
      isError: query.isError,
      isLoading: query.isLoading,
      isFetching: query.isFetching,
      isFetched: query.isFetched,
      isSuccess: query.isSuccess,
      status: query.status,
      fetchStatus: query.fetchStatus,
      refetch: query.refetch,
    };
  }

  return query;
};
