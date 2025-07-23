import React from "react";
import { Provider } from "#/types/settings";
import { useConfig } from "./use-config";
import { useUserRepositories } from "./use-user-repositories";
import { useInstallationRepositories } from "./use-installation-repositories";

/**
 * Hook that determines which repository hook to use based on provider and app mode:
 * - Bitbucket: Always use installation repositories
 * - GitLab: Always use user repositories
 * - GitHub: Use user repositories in OSS mode, installation repositories in SaaS mode
 */
export const useRepositories = (selectedProvider: Provider | null) => {
  const { data: config } = useConfig();

  // Determine which hook to use based on provider and app mode
  const shouldUseInstallationRepos = React.useMemo(() => {
    if (!selectedProvider) return false;

    switch (selectedProvider) {
      case "bitbucket":
        return true;
      case "gitlab":
        return false;
      case "github":
        return config?.APP_MODE === "saas";
      default:
        return false;
    }
  }, [selectedProvider, config?.APP_MODE]);

  // Only call the appropriate hook based on the provider and app mode
  const userRepos = !shouldUseInstallationRepos ? useUserRepositories(selectedProvider) : null;
  const installationRepos = shouldUseInstallationRepos ? useInstallationRepositories(selectedProvider) : null;

  // Return the active repository data
  return shouldUseInstallationRepos ? installationRepos! : userRepos!;
};
