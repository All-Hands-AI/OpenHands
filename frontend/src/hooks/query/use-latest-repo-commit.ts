import { useQuery } from "@tanstack/react-query";
import { retrieveLatestGitHubCommit, isGitHubErrorReponse } from "#/api/github";

interface UseLatestRepoCommitConfig {
  gitHubToken: string | null;
  repository: string | null;
}

export const useLatestRepoCommit = (config: UseLatestRepoCommitConfig) =>
  useQuery({
    queryKey: ["latest_commit", config.gitHubToken, config.repository],
    queryFn: async () => {
      const data = await retrieveLatestGitHubCommit(
        config.gitHubToken!,
        config.repository!,
      );

      if (isGitHubErrorReponse(data)) {
        throw new Error("Failed to retrieve latest commit");
      }

      return data[0];
    },
    enabled: !!config.gitHubToken && !!config.repository,
  });
