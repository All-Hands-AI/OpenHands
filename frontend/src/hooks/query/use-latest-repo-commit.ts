import { useQuery } from "@tanstack/react-query";
import { retrieveLatestGitHubCommit, isGitHubErrorReponse } from "#/api/github";
import { useAuth } from "#/context/auth-context";

interface UseLatestRepoCommitConfig {
  repository: string | null;
}

export const useLatestRepoCommit = (config: UseLatestRepoCommitConfig) => {
  const { gitHubToken, refreshToken, logout } = useAuth();

  return useQuery({
    queryKey: ["latest_commit", gitHubToken, config.repository],
    queryFn: async () => {
      const data = await retrieveLatestGitHubCommit(
        gitHubToken!,
        refreshToken,
        logout,
        config.repository!,
      );

      if (isGitHubErrorReponse(data)) {
        throw new Error("Failed to retrieve latest commit");
      }

      return data[0];
    },
    enabled: !!gitHubToken && !!config.repository,
  });
};
