import { useInfiniteQuery } from "@tanstack/react-query";
import {
  isGitHubErrorReponse,
  retrieveGitHubUserRepositories,
} from "#/api/github";
import { extractNextPageFromLink } from "#/utils/extract-next-page-from-link";

interface UserRepositoriesQueryFnProps {
  pageParam: number;
  ghToken: string;
}

const userRepositoriesQueryFn = async ({
  pageParam,
  ghToken,
}: UserRepositoriesQueryFnProps) => {
  const response = await retrieveGitHubUserRepositories(ghToken, pageParam);

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

export const useUserRepositories = (ghToken: string | null) =>
  useInfiniteQuery({
    queryKey: ["repositories", ghToken],
    queryFn: async ({ pageParam }) =>
      userRepositoriesQueryFn({ pageParam, ghToken: ghToken! }), // only called when ghToken is not null
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled: !!ghToken,
    select: (data) => data.pages.flatMap((page) => page.data),
  });
