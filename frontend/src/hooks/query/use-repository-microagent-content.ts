import { useQuery } from "@tanstack/react-query";
import GitService from "#/api/git-service/git-service.api";

export const useRepositoryMicroagentContent = (
  owner: string,
  repo: string,
  filePath: string,
  cacheDisabled: boolean = false,
) =>
  useQuery({
    queryKey: ["repository", "microagent", "content", owner, repo, filePath],
    queryFn: () =>
      GitService.getRepositoryMicroagentContent(owner, repo, filePath),
    enabled: !!owner && !!repo && !!filePath,
    staleTime: cacheDisabled ? 0 : 1000 * 60 * 5, // 5 minutes
    gcTime: cacheDisabled ? 0 : 1000 * 60 * 15, // 15 minutes
  });
