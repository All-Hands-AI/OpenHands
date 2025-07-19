import { GitProviderIcon } from "#/components/shared/git-provider-icon";
import { GitRepository } from "#/types/git";
import { MicroagentManagementAddMicroagentButton } from "./microagent-management-add-microagent-button";

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
        <div
          className="text-white text-base font-normal truncate max-w-[168px]"
          title={repository.full_name}
        >
          {repository.full_name}
        </div>
      </div>
      <MicroagentManagementAddMicroagentButton />
    </div>
  );
}
