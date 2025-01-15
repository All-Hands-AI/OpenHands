import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import { retrieveGitHubUserRepositories } from "#/api/github";
import { useConfig } from "./use-config";
import { useSettings } from "./use-settings";

export const useUserRepositories = () => {
  const { data: settings } = useSettings();
  const { data: config } = useConfig();

  const repos = useInfiniteQuery({
    queryKey: ["repositories", settings?.GITHUB_TOKEN_IS_SET],
    queryFn: async ({ pageParam }) =>
      retrieveGitHubUserRepositories(pageParam, 100),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled: !!settings?.GITHUB_TOKEN_IS_SET && config?.APP_MODE === "oss",
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
