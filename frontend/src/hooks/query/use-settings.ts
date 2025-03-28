import { useQuery } from "@tanstack/react-query";
import React from "react";
import posthog from "posthog-js";
import { useAuth } from "#/context/auth-context";
import { SettingsService } from "#/api/settings-service/settings-service.api";
import { ClientUserSettings } from "#/api/settings-service/settings-service.types";
import { DEFAULT_SETTINGS } from "#/services/settings";

const settingsQueryFn = async (): Promise<ClientUserSettings> => {
  const settings = await SettingsService.getSettings();
  return { ...settings, is_new_user: false };
};

export const useSettings = () => {
  const { setGitHubTokenIsSet, githubTokenIsSet } = useAuth();

  const query = useQuery({
    queryKey: ["settings", githubTokenIsSet],
    queryFn: settingsQueryFn,
    // Only retry if the error is not a 404 because we
    // would want to show the modal immediately if the
    // settings are not found
    retry: (_, error) => error.status !== 404,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
    meta: {
      disableToast: true,
    },
  });

  React.useEffect(() => {
    if (query.isFetched && query.data?.llm_api_key) {
      posthog.capture("user_activated");
    }
  }, [query.data?.llm_api_key, query.isFetched]);

  React.useEffect(() => {
    if (query.isFetched) setGitHubTokenIsSet(!!query.data?.github_token_is_set);
  }, [query.data?.github_token_is_set, query.isFetched]);

  if (query.error?.status === 404) {
    // Object rest destructuring on a query will observe all changes to the query, leading to excessive re-renders.
    // Only return the specific properties we need to avoid this.
    return {
      data: DEFAULT_SETTINGS,
      error: query.error,
      isError: query.isError,
      isLoading: query.isLoading,
      isFetched: query.isFetched,
      isFetching: query.isFetching,
      isSuccess: query.isSuccess,
    };
  }

  return query;
};
