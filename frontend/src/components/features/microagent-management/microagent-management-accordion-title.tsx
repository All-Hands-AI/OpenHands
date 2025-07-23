import { GitProviderIcon } from "#/components/shared/git-provider-icon";
import { GitRepository } from "#/types/git";
import { MicroagentManagementAddMicroagentButton } from "./microagent-management-add-microagent-button";
import { TooltipButton } from "#/components/shared/buttons/tooltip-button";

interface MicroagentManagementAccordionTitleProps {
  repository: GitRepository;
}

export function MicroagentManagementAccordionTitle({
  repository,
}: MicroagentManagementAccordionTitleProps) {
  const repoName = repository.full_name;
  const isLong = repoName.length > 25;
  const displayName = isLong ? `${repoName.slice(0, 25)}...` : repoName;

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <GitProviderIcon gitProvider={repository.git_provider} />
        <TooltipButton
          tooltip={repoName}
          ariaLabel={repoName}
          className="text-white text-base font-normal bg-transparent p-0 min-w-0 h-auto cursor-pointer"
          testId="repository-name-tooltip"
          placement="bottom"
        >
          <span>{displayName}</span>
        </TooltipButton>
      </div>
      <MicroagentManagementAddMicroagentButton repository={repository} />
    </div>
  );
}
