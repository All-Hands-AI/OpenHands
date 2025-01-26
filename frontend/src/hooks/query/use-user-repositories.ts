import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import { retrieveGitHubUserRepositories } from "#/api/github";
import { useAuth } from "#/context/auth-context";
import { useConfig } from "./use-config";

export const useUserRepositories = () => {
  const { gitHubToken } = useAuth();
  const { data: config } = useConfig();

  const repos = useInfiniteQuery({
    queryKey: ["repositories", gitHubToken],
    queryFn: async ({ pageParam }) =>
      retrieveGitHubUserRepositories(pageParam, 100),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled: !!gitHubToken && config?.APP_MODE === "oss",
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
