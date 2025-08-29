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
        const { repoPage, installationIndex, _timestamp } = pageParam as {
          installationIndex: number | null;
          repoPage: number | null;
          _timestamp?: number;
        };

        if (!installations) {
          throw new Error("Missing installation list");
        }

        console.log('🔧 FETCH: Requesting repos', {
          provider,
          installationIndex: installationIndex || 0,
          installations: installations?.map((id, idx) => `${idx}:${id}`),
          repoPage: repoPage || 1,
          pageSize,
          timestamp: _timestamp,
        });
        console.log('🔧 FETCH: Raw pageParam received:', pageParam);

        const result = await OpenHands.retrieveInstallationRepositories(
          provider,
          installationIndex || 0,
          installations,
          repoPage || 1,
          pageSize,
        );

        console.log('🔧 FETCH: Received repos', {
          installationIndex: installationIndex || 0,
          repoPage: repoPage || 1,
          dataCount: result.data.length,
          repos: result.data.map(r => r.full_name),
          nextPage: result.nextPage,
          nextInstallationIndex: result.installationIndex,
        });

        return result;
      }

      return OpenHands.retrieveUserGitRepositories(
        provider,
        pageParam as number,
        pageSize,
      );
    },
    getNextPageParam: (lastPage) => {
      if (useInstallationRepos) {
        const installationPage = lastPage as InstallationRepositoriesResponse;

        console.log('🔧 PAGINATION: Determining next page', {
          currentNextPage: installationPage.nextPage,
          currentInstallationIndex: installationPage.installationIndex,
          dataLength: installationPage.data.length,
        });

        if (installationPage.nextPage) {
          const nextParam = {
            installationIndex: installationPage.installationIndex,
            repoPage: installationPage.nextPage,
          };
          console.log('🔧 PAGINATION: Next page within installation', nextParam);
          return nextParam;
        }

        if (installationPage.installationIndex !== null) {
          // Validate that the next installation index is within bounds
          if (installations && installationPage.installationIndex >= installations.length) {
            console.log('🔧 PAGINATION: Installation index out of bounds, stopping', {
              installationIndex: installationPage.installationIndex,
              installationsLength: installations.length
            });
            return null;
          }

          const nextParam = {
            installationIndex: installationPage.installationIndex,
            repoPage: 1,
            // Add a unique identifier to ensure React Query treats this as a new request
            _timestamp: Date.now(),
          };
          console.log('🔧 PAGINATION: Moving to next installation', nextParam);
          console.log('🔧 PAGINATION: Current installations array:', installations?.map((id, idx) => `${idx}:${id}`));
          console.log('🔧 PAGINATION: Will fetch installation at index:', installationPage.installationIndex);
          return nextParam;
        }

        console.log('🔧 PAGINATION: No more pages');
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
