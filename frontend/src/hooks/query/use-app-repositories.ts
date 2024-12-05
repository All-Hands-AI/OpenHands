import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import {
  isGitHubErrorReponse,
  retrieveGitHubUserRepositories,
} from "#/api/github";
import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";
import { useAuth } from "#/context/auth-context";
import { useAppIntallations } from "./use-app-installations";

interface appRepositoriesQueryFnProps {
  pageParam: {
    installationIndex: number; // Tracks the current installation
    repoPage: number; // Tracks the current repository page for that installation
  };
  ghToken: string;
  appInstallations: string[];
}

const appRepositoriesQueryFn = async ({
  pageParam: { installationIndex, repoPage },
  ghToken,
  appInstallations,
}: appRepositoriesQueryFnProps) => {
  const response = await retrieveGitHubUserRepositories(
    ghToken,
    repoPage,
    100,
    appInstallations[installationIndex],
  );

  if (!response.ok) {
    throw new Error("Failed to fetch repositories");
  }

  const data = (await response.json()).repositories as
    | GitHubRepository
    | GitHubErrorReponse;

  if (isGitHubErrorReponse(data)) {
    throw new Error(data.message);
  }

  const link = response.headers.get("link") ?? "";
  const nextPage = extractNextPageFromLink(link);
  const nextInstallation =
    !nextPage && installationIndex + 1 < appInstallations.length
      ? installationIndex + 1
      : null;

  return {
    data,
    nextPage,
    nextInstallation,
    installationIndex,
  };
};

export const useAppRepositories = () => {
  const { gitHubToken } = useAuth();
  const { data: installations } = useAppIntallations();

  const repos = useInfiniteQuery({
    queryKey: ["repositories", gitHubToken, installations],
    queryFn: async ({ pageParam }) =>
      appRepositoriesQueryFn({
        pageParam: pageParam || { installationIndex: 0, repoPage: 1 },
        ghToken: gitHubToken!,
        appInstallations: installations || [],
      }),

    initialPageParam: { installationIndex: 0, repoPage: 1 },
    getNextPageParam: (lastPage) => {
      if (lastPage.nextPage) {
        return {
          installationIndex: lastPage.installationIndex,
          repoPage: lastPage.nextPage,
        };
      }

      if (lastPage.nextInstallation !== null) {
        return { installationIndex: lastPage.nextInstallation, repoPage: 1 };
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
