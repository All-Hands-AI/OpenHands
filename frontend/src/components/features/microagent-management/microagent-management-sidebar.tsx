import { useEffect } from "react";
import { useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import { MicroagentManagementSidebarHeader } from "./microagent-management-sidebar-header";
import { MicroagentManagementSidebarTabs } from "./microagent-management-sidebar-tabs";
import { useUserRepositories } from "#/hooks/query/use-user-repositories";
import {
  setPersonalRepositories,
  setOrganizationRepositories,
  setRepositories,
} from "#/state/microagent-management-slice";
import { GitRepository } from "#/types/git";
import { LoadingSpinner } from "#/components/shared/loading-spinner";

export function MicroagentManagementSidebar() {
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const { data: repositories, isLoading } = useUserRepositories();

  useEffect(() => {
    if (repositories) {
      const personalRepos: GitRepository[] = [];
      const organizationRepos: GitRepository[] = [];
      const otherRepos: GitRepository[] = [];

      repositories.forEach((repo: GitRepository) => {
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
    <div className="w-[418px] h-full max-h-full overflow-y-auto overflow-x-hidden border-r border-[#525252] bg-[#24272E] rounded-tl-lg rounded-bl-lg py-10 px-6 flex flex-col">
      <MicroagentManagementSidebarHeader />
      {isLoading ? (
        <div className="flex flex-col items-center justify-center gap-4 flex-1">
          <LoadingSpinner size="small" />
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
