import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import { retrieveGitHubAppRepositories } from "#/api/github";
import { useAuth } from "#/context/auth-context";
import { useAppInstallations } from "./use-app-installations";

export const useAppRepositories = () => {
  const { gitHubToken } = useAuth();
  const { data: installations } = useAppInstallations();

  const repos = useInfiniteQuery({
    queryKey: ["repositories", gitHubToken, installations],
    queryFn: async ({
      pageParam,
    }: {
      pageParam: { installation_index: number | null; repoPage: number | null };
    }) => {
      const { repoPage, installation_index } = pageParam;

      if (!installations) {
        throw new Error("Missing installation list");
      }

      return retrieveGitHubAppRepositories(
        repoPage || 1,
        30,
        installation_index || 0,
        installations,
      );
    },
    initialPageParam: { installation_index: 0, repoPage: 1 },
    getNextPageParam: (lastPage) => {
      if (lastPage.nextPage) {
        return {
          installation_index: lastPage.installation_index,
          repoPage: lastPage.nextPage,
        };
      }

      if (lastPage.installation_index !== null) {
        return { installation_index: lastPage.installation_index, repoPage: 1 };
      }

      return null;
    },
    enabled:
      !!gitHubToken && Array.isArray(installations) && installations.length > 0,
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
