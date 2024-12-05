import { useQuery } from "@tanstack/react-query";
import { retrieveLatestGitHubCommit } from "#/api/github";
import { useAuth } from "#/context/auth-context";

interface UseLatestRepoCommitConfig {
  repository: string | null;
}

export const useLatestRepoCommit = (config: UseLatestRepoCommitConfig) => {
  const { gitHubToken } = useAuth();

  return useQuery({
    queryKey: ["latest_commit", gitHubToken, config.repository],
    queryFn: () => retrieveLatestGitHubCommit(config.repository!),
    enabled: !!gitHubToken && !!config.repository,
  });
};
