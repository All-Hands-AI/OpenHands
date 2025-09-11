import { useQuery } from "@tanstack/react-query";
import UserService from "#/api/user-service/user-service.api";

export const useRepositoryMicroagents = (
  owner: string,
  repo: string,
  cacheDisabled: boolean = false,
) =>
  useQuery({
    queryKey: ["repository", "microagents", owner, repo],
    queryFn: () => UserService.getRepositoryMicroagents(owner, repo),
    enabled: !!owner && !!repo,
    staleTime: cacheDisabled ? 0 : 1000 * 60 * 5, // 5 minutes
    gcTime: cacheDisabled ? 0 : 1000 * 60 * 15, // 15 minutes
  });
