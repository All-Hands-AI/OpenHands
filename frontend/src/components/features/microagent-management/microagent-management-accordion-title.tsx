import { GitProviderIcon } from "#/components/shared/git-provider-icon";
import { GitRepository } from "#/types/git";
import { MicroagentManagementAddMicroagentButton } from "./microagent-management-add-microagent-button";
import { UnifiedButton } from "#/ui/unified-button/unified-button";

interface MicroagentManagementAccordionTitleProps {
  repository: GitRepository;
}

export function MicroagentManagementAccordionTitle({
  repository,
}: MicroagentManagementAccordionTitleProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <GitProviderIcon gitProvider={repository.git_provider} />
        <UnifiedButton
          withTooltip
          tooltipContent={repository.full_name}
          ariaLabel={repository.full_name}
          className="text-white text-base font-normal bg-transparent p-0 min-w-0 h-auto cursor-pointer translate-y-[-1px] hover:bg-transparent text-left justify-start"
          testId="repository-name-tooltip"
          tooltipProps={{ placement: "bottom" }}
        >
          <span className="truncate max-w-[194px]">{repository.full_name}</span>
        </UnifiedButton>
      </div>
      <MicroagentManagementAddMicroagentButton repository={repository} />
    </div>
  );
}
