import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import { Spinner } from "@heroui/react";
import { MicroagentManagementSidebarHeader } from "./microagent-management-sidebar-header";
import { MicroagentManagementSidebarTabs } from "./microagent-management-sidebar-tabs";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import { useUserProviders } from "#/hooks/use-user-providers";
import {
  setPersonalRepositories,
  setOrganizationRepositories,
  setRepositories,
} from "#/state/microagent-management-slice";
import { GitRepository } from "#/types/git";
import { cn } from "#/utils/utils";

interface MicroagentManagementSidebarProps {
  isSmallerScreen?: boolean;
}

export function MicroagentManagementSidebar({
  isSmallerScreen = false,
}: MicroagentManagementSidebarProps) {
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const { providers } = useUserProviders();
  const selectedProvider = providers.length > 0 ? providers[0] : null;
  const { data: repositories, isLoading } =
    useUserRepositories(selectedProvider);

  useEffect(() => {
    if (repositories?.pages) {
      const personalRepos: GitRepository[] = [];
      const organizationRepos: GitRepository[] = [];
      const otherRepos: GitRepository[] = [];

      // Flatten all pages to get all repositories
      const allRepositories = repositories.pages.flatMap((page) => page.data);

      allRepositories.forEach((repo: GitRepository) => {
        const hasOpenHandsSuffix = repo.full_name.endsWith("/.openhands");

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
  }, [repositories, dispatch]);

  return (
    <div
      className={cn(
        "w-[418px] h-full max-h-full overflow-y-auto overflow-x-hidden border-r border-[#525252] bg-[#24272E] rounded-tl-lg rounded-bl-lg py-10 px-6 flex flex-col",
        isSmallerScreen && "w-full border-none",
      )}
    >
      <MicroagentManagementSidebarHeader />
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
