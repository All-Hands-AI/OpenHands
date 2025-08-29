import { useInfiniteQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import { useUserProviders } from "../use-user-providers";
import { GitRepository } from "../../types/git";
import { Provider } from "../../types/settings";
import OpenHands from "#/api/open-hands";
import { shouldUseInstallationRepos } from "#/utils/utils";

interface UseGitRepositoriesOptions {
  provider: Provider | null;
  pageSize?: number;
  enabled?: boolean;
  installations?: string[];
}

interface UserRepositoriesResponse {
  data: GitRepository[];
  nextPage: number | null;
}

interface InstallationRepositoriesResponse {
  data: GitRepository[];
  nextPage: number | null;
  installationIndex: number | null;
}

export function useGitRepositories(options: UseGitRepositoriesOptions) {
  const { provider, pageSize = 30, enabled = true, installations } = options;
  const { providers } = useUserProviders();
  const { data: config } = useConfig();

  const useInstallationRepos = provider
    ? shouldUseInstallationRepos(provider, config?.APP_MODE)
    : false;

  const repos = useInfiniteQuery<
    UserRepositoriesResponse | InstallationRepositoriesResponse
  >({
    queryKey: [
      "repositories",
      providers || [],
      provider,
      useInstallationRepos,
      pageSize,
      ...(useInstallationRepos ? [installations || []] : []),
    ],
    queryFn: async ({ pageParam }) => {
      if (!provider) {
        throw new Error("Provider is required");
      }

      if (useInstallationRepos) {
        const { repoPage, installationIndex, _pageCount } = pageParam as {
          installationIndex: number | null;
          repoPage: number | null;
          _pageCount?: number;
        };

        if (!installations) {
          throw new Error("Missing installation list");
        }



        const result = await OpenHands.retrieveInstallationRepositories(
          provider,
          installationIndex || 0,
          installations,
          repoPage || 1,
          pageSize,
        );



        return result;
      }

      return OpenHands.retrieveUserGitRepositories(
        provider,
        pageParam as number,
        pageSize,
      );
    },
    getNextPageParam: (lastPage, allPages) => {
      if (useInstallationRepos) {
        const installationPage = lastPage as InstallationRepositoriesResponse;



        // If there are more pages in the current installation, fetch them
        if (installationPage.nextPage) {
          return {
            installationIndex: installationPage.installationIndex,
            repoPage: installationPage.nextPage,
          };
        }

        // If there are more installations to fetch, move to the next one
        if (installationPage.installationIndex !== null) {
          // Validate that the next installation index is within bounds
          if (installations && installationPage.installationIndex >= installations.length) {
            return null;
          }

          // Create a unique pagination parameter that React Query will recognize as different
          return {
            installationIndex: installationPage.installationIndex,
            repoPage: 1,
            // Use page count to ensure uniqueness instead of timestamp
            _pageCount: allPages.length,
          };
        }

        return null;
      }

      const userPage = lastPage as UserRepositoriesResponse;
      return userPage.nextPage;
    },
    initialPageParam: useInstallationRepos
      ? { installationIndex: 0, repoPage: 1 }
      : 1,
    enabled:
      enabled &&
      (providers || []).length > 0 &&
      !!provider &&
      (!useInstallationRepos ||
        (Array.isArray(installations) && installations.length > 0)),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
    refetchOnWindowFocus: false,
  });

  const onLoadMore = () => {
    if (repos.hasNextPage && !repos.isFetchingNextPage) {
      repos.fetchNextPage();
    }
  };

  return {
    data: repos.data,
    isLoading: repos.isLoading,
    isError: repos.isError,
    hasNextPage: repos.hasNextPage,
    isFetchingNextPage: repos.isFetchingNextPage,
    fetchNextPage: repos.fetchNextPage,
    onLoadMore,
  };
}
