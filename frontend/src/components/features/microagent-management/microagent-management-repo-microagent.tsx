import {
  Microagent,
  MicroagentManagementMicroagentCard,
} from "./microagent-management-microagent-card";
import { MicroagentManagementLearnThisRepo } from "./microagent-management-learn-this-repo";
import { MicroagentManagementAddMicroagentButton } from "./microagent-management-add-microagent-button";

export interface RepoMicroagent {
  id: string;
  repositoryName: string;
  repositoryUrl: string;
  microagents: Microagent[];
}

interface MicroagentManagementRepoMicroagentProps {
  repoMicroagent: RepoMicroagent;
}

export function MicroagentManagementRepoMicroagent({
  repoMicroagent,
}: MicroagentManagementRepoMicroagentProps) {
  const { microagents } = repoMicroagent;
  const numberOfMicroagents = microagents.length;

  return (
    <div className="pb-12">
      <div className="flex items-center justify-between pb-4">
        <div className="text-white text-base font-normal">
          {repoMicroagent.repositoryName}
        </div>
        <MicroagentManagementAddMicroagentButton />
      </div>
      {numberOfMicroagents === 0 && (
        <MicroagentManagementLearnThisRepo
          repositoryUrl={repoMicroagent.repositoryUrl}
        />
      )}
      {numberOfMicroagents > 0 && (
        <>
          {microagents.map((microagent) => (
            <div key={microagent.id} className="pb-4 last:pb-0">
              <MicroagentManagementMicroagentCard microagent={microagent} />
            </div>
          ))}
        </>
      )}
    </div>
  );
}
