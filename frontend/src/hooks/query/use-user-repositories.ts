import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import {
  isGitHubErrorReponse,
  retrieveGitHubUserRepositories,
} from "#/api/github";
import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";
import { useAuth } from "#/context/auth-context";
import { useAppIntallations } from "./use-app-installations";

interface UserRepositoriesQueryFnProps {
  pageParam: {
    installationIndex: number; // Tracks the current installation
    repoPage: number; // Tracks the current repository page for that installation
  };
  ghToken: string;
  appInstallations: string[];
}

const userRepositoriesQueryFn = async ({
  pageParam: { installationIndex, repoPage },
  ghToken,
  appInstallations,
}: UserRepositoriesQueryFnProps) => {
  const response = await retrieveGitHubUserRepositories(
    ghToken,
    appInstallations[installationIndex],
    repoPage,
    100,
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

export const useUserRepositories = () => {
  const { gitHubToken } = useAuth();
  const { data: installations } = useAppIntallations();

  const repos = useInfiniteQuery({
    queryKey: ["repositories", gitHubToken, installations],
    queryFn: async ({ pageParam }) =>
      userRepositoriesQueryFn({
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
    enabled: !!gitHubToken && !!installations?.length,
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
