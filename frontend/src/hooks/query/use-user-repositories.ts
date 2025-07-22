import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import { useConfig } from "./use-config";
import { useUserProviders } from "../use-user-providers";
import { Provider } from "#/types/settings";
import OpenHands from "#/api/open-hands";
import { shouldUseInstallationRepos } from "#/utils/utils";

export const useUserRepositories = (selected_provider: Provider | null) => {
  const { providers } = useUserProviders();
  const { data: config } = useConfig();

  const repos = useInfiniteQuery({
    queryKey: ["repositories", providers, selected_provider],
    queryFn: async ({ pageParam }) =>
      OpenHands.retrieveUserGitRepositories(selected_provider!, pageParam, 100),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled:
      providers.length > 0 &&
      !!selected_provider &&
      !shouldUseInstallationRepos(selected_provider, config?.APP_MODE),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });

  const { isSuccess, isFetchingNextPage, hasNextPage, fetchNextPage } = repos;
  React.useEffect(() => {
    if (!isFetchingNextPage && isSuccess && hasNextPage) {
      fetchNextPage();
    }
  }, [isFetchingNextPage, isSuccess, hasNextPage, fetchNextPage]);

  return repos;
};
