import { useEffect, useState, useMemo } from "react";
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
import { sanitizeQuery } from "#/utils/sanitize-query";
import { I18nKey } from "#/i18n/declaration";
import { getGitProviderMicroagentManagementCustomStyles } from "#/components/common/react-select-styles";

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

  const [searchQuery, setSearchQuery] = useState("");

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
    setSearchQuery("");
  };

  // Filter repositories based on search query
  const filteredRepositories = useMemo(() => {
    if (!repositories?.pages) return null;

    // Flatten all pages to get all repositories
    const allRepositories = repositories.pages.flatMap((page) => page.data);

    if (!searchQuery.trim()) {
      return allRepositories;
    }

    const sanitizedQuery = sanitizeQuery(searchQuery);
    return allRepositories.filter((repository: GitRepository) => {
      const sanitizedRepoName = sanitizeQuery(repository.full_name);
      return sanitizedRepoName.includes(sanitizedQuery);
    });
  }, [repositories, searchQuery, selectedProvider]);

  useEffect(() => {
    if (!filteredRepositories?.length) {
      dispatch(setPersonalRepositories([]));
      dispatch(setOrganizationRepositories([]));
      dispatch(setRepositories([]));
      return;
    }

    const personalRepos: GitRepository[] = [];
    const organizationRepos: GitRepository[] = [];
    const otherRepos: GitRepository[] = [];

    filteredRepositories.forEach((repo: GitRepository) => {
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
  }, [filteredRepositories, selectedProvider, dispatch]);

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
            classNamePrefix="git-provider-dropdown"
            styles={getGitProviderMicroagentManagementCustomStyles()}
          />
        </div>
      )}

      {/* Search Input */}
      <div className="flex flex-col gap-2 w-full mt-6">
        <label htmlFor="repository-search" className="sr-only">
          {t(I18nKey.COMMON$SEARCH_REPOSITORIES)}
        </label>
        <input
          id="repository-search"
          name="repository-search"
          type="text"
          placeholder={`${t(I18nKey.COMMON$SEARCH_REPOSITORIES)}...`}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className={cn(
            "bg-tertiary border border-[#717888] bg-[#454545] w-full rounded-sm p-2 placeholder:italic placeholder:text-tertiary-alt",
            "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed h-10 box-shadow-none outline-none",
          )}
        />
      </div>

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
