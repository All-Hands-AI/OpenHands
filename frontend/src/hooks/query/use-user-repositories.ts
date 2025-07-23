import { useInfiniteQuery } from "@tanstack/react-query";
import { useConfig } from "./use-config";
import { useUserProviders } from "../use-user-providers";
import { Provider } from "#/types/settings";
import OpenHands from "#/api/open-hands";
import { shouldUseInstallationRepos } from "#/utils/utils";
import { useInfiniteScroll } from "@heroui/use-infinite-scroll";
import { useRef, useState } from "react";

export const useUserRepositories = (selectedProvider: Provider | null) => {
  const { providers } = useUserProviders();
  const { data: config } = useConfig();
  const [isOpen, setIsOpen] = useState(false);

  const repos = useInfiniteQuery({
    queryKey: ["repositories", providers, selectedProvider],
    queryFn: async ({ pageParam }) =>
      OpenHands.retrieveUserGitRepositories(selectedProvider!, pageParam, 30),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => lastPage.nextPage,
    enabled:
      providers.length > 0 &&
      !!selectedProvider &&
      !shouldUseInstallationRepos(selectedProvider, config?.APP_MODE),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });

  // Use the infinite scroll hook to handle loading more data
  const [_, scrollRef] = useInfiniteScroll({
    hasMore: repos.hasNextPage || false,
    isEnabled: isOpen,
    shouldUseLoader: false,
    onLoadMore: () => {
      if (repos.hasNextPage && !repos.isFetchingNextPage) {
        repos.fetchNextPage();
      }
    },
  });

  // Return the query result with the scroll ref
  return {
    data: repos.data,
    isLoading: repos.isLoading,
    isError: repos.isError,
    hasNextPage: repos.hasNextPage,
    isFetchingNextPage: repos.isFetchingNextPage,
    fetchNextPage: repos.fetchNextPage,
    scrollRef,
    onOpenChange: setIsOpen,
  };
};
