import { useQuery } from "@tanstack/react-query";
import GitService from "#/api/git-service/git-service.api";

export const useRepositoryMicroagents = (
  owner: string,
  repo: string,
  cacheDisabled: boolean = false,
) =>
  useQuery({
    queryKey: ["repository", "microagents", owner, repo],
    queryFn: () => GitService.getRepositoryMicroagents(owner, repo),
    enabled: !!owner && !!repo,
    staleTime: cacheDisabled ? 0 : 1000 * 60 * 5, // 5 minutes
    gcTime: cacheDisabled ? 0 : 1000 * 60 * 15, // 15 minutes
  });
