import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import { retrieveUserGitRepositories } from "#/api/git";
import { useConfig } from "./use-config";
import { useAuth } from "#/context/auth-context";

export const useUserRepositories = () => {
  const { providerTokensSet, providersAreSet } = useAuth();
  const { data: config } = useConfig();

  const repos = useInfiniteQuery({
    queryKey: ["repositories", providerTokensSet],
    queryFn: async ({ pageParam }) =>
      retrieveUserGitRepositories(pageParam, 100),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled: providersAreSet && config?.APP_MODE === "oss",
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });

  // TODO: Once we create our custom dropdown component, we should fetch data onEndReached
  // (nextui autocomplete doesn't support onEndReached nor is it compatible for extending)
  const { isSuccess, isFetchingNextPage, hasNextPage, fetchNextPage } = repos;
  React.useEffect(() => {
    if (!isFetchingNextPage && isSuccess && hasNextPage) {
      fetchNextPage();
    }
  }, [isFetchingNextPage, isSuccess, hasNextPage, fetchNextPage]);

  return repos;
};
