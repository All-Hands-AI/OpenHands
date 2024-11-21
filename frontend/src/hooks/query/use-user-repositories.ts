import { useInfiniteQuery } from "@tanstack/react-query";
import React from "react";
import {
  isGitHubErrorReponse,
  retrieveGitHubUserRepositories,
} from "#/api/github";
import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";
import { useAuth } from "#/context/auth-context";

interface UserRepositoriesQueryFnProps {
  pageParam: number;
  ghToken: string;
}

const userRepositoriesQueryFn = async ({
  pageParam,
  ghToken,
}: UserRepositoriesQueryFnProps) => {
  const response = await retrieveGitHubUserRepositories(
    ghToken,
    pageParam,
    100,
  );

  if (!response.ok) {
    throw new Error("Failed to fetch repositories");
  }

  const data = (await response.json()) as GitHubRepository | GitHubErrorReponse;

  if (isGitHubErrorReponse(data)) {
    throw new Error(data.message);
  }

  const link = response.headers.get("link") ?? "";
  const nextPage = extractNextPageFromLink(link);

  return { data, nextPage };
};

export const useUserRepositories = () => {
  const { gitHubToken } = useAuth();

  const repos = useInfiniteQuery({
    queryKey: ["repositories", gitHubToken],
    queryFn: async ({ pageParam }) =>
      userRepositoriesQueryFn({ pageParam, ghToken: gitHubToken! }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled: !!gitHubToken,
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
