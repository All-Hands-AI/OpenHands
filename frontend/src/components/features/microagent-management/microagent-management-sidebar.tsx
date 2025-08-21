import { useEffect, useState } from "react";
import { useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import { Spinner } from "@heroui/react";
import { MicroagentManagementSidebarHeader } from "./microagent-management-sidebar-header";
import { MicroagentManagementSidebarTabs } from "./microagent-management-sidebar-tabs";
import { useGitRepositories } from "#/hooks/query/use-git-repositories";
import { useUserProviders } from "#/hooks/use-user-providers";
import { GitProviderDropdown } from "#/components/common/git-provider-dropdown";
import {
  setPersonalRepositories,
  setOrganizationRepositories,
  setRepositories,
} from "#/state/microagent-management-slice";
import { GitRepository } from "#/types/git";
import { Provider } from "#/types/settings";
import { cn } from "#/utils/utils";

interface MicroagentManagementSidebarProps {
  isSmallerScreen?: boolean;
}

export function MicroagentManagementSidebar({
  isSmallerScreen = false,
}: MicroagentManagementSidebarProps) {
  const { providers } = useUserProviders();

  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(
    providers.length > 0 ? providers[0] : null,
  );

  const dispatch = useDispatch();

  const { t } = useTranslation();

  const { data: repositories, isLoading } = useGitRepositories({
    provider: selectedProvider,
    pageSize: 200,
    enabled: !!selectedProvider,
  });

  // Auto-select provider if there's only one
  useEffect(() => {
    if (providers.length > 0 && !selectedProvider) {
      setSelectedProvider(providers[0]);
    }
  }, [providers, selectedProvider]);

  const handleProviderChange = (provider: Provider | null) => {
    setSelectedProvider(provider);
  };

  useEffect(() => {
    if (repositories?.pages) {
      const personalRepos: GitRepository[] = [];
      const organizationRepos: GitRepository[] = [];
      const otherRepos: GitRepository[] = [];

      // Flatten all pages to get all repositories
      const allRepositories = repositories.pages.flatMap((page) => page.data);

      allRepositories.forEach((repo: GitRepository) => {
        const hasOpenHandsSuffix =
          selectedProvider === "gitlab"
            ? repo.full_name.endsWith("/openhands-config")
            : repo.full_name.endsWith("/.openhands");

        if (repo.owner_type === "user" && hasOpenHandsSuffix) {
          personalRepos.push(repo);
        } else if (repo.owner_type === "organization" && hasOpenHandsSuffix) {
          organizationRepos.push(repo);
        } else {
          otherRepos.push(repo);
        }
      });

      dispatch(setPersonalRepositories(personalRepos));
      dispatch(setOrganizationRepositories(organizationRepos));
      dispatch(setRepositories(otherRepos));
    }
  }, [repositories, selectedProvider, dispatch]);

  return (
    <div
      className={cn(
        "w-[418px] h-full max-h-full overflow-y-auto overflow-x-hidden border-r border-[#525252] bg-[#24272E] rounded-tl-lg rounded-bl-lg py-10 px-6 flex flex-col",
        isSmallerScreen && "w-full border-none",
      )}
    >
      <MicroagentManagementSidebarHeader />

      {/* Provider Selection */}
      {providers.length > 1 && (
        <div className="mt-6">
          <GitProviderDropdown
            providers={providers}
            value={selectedProvider}
            placeholder="Select Provider"
            onChange={handleProviderChange}
            className="w-full"
          />
        </div>
      )}

      {isLoading ? (
        <div className="flex flex-col items-center justify-center gap-4 flex-1">
          <Spinner size="sm" />
          <span className="text-sm text-white">
            {t("HOME$LOADING_REPOSITORIES")}
          </span>
        </div>
      ) : (
        <MicroagentManagementSidebarTabs />
      )}
    </div>
  );
}
