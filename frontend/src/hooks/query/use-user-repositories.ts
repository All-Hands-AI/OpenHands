import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import { retrieveUserGitRepositories } from "#/api/git";
import { useAuth } from "#/context/auth-context";

export const useUserRepositories = () => {
  const { providerTokensSet, providersAreSet } = useAuth();

  const repos = useInfiniteQuery({
    queryKey: ["repositories", providerTokensSet],
    queryFn: async () => retrieveUserGitRepositories(),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled: providersAreSet,
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
