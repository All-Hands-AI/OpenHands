import { MicroagentManagementMicroagentCard } from "./microagent-management-microagent-card";
import { MicroagentManagementLearnThisRepo } from "./microagent-management-learn-this-repo";
import { useRepositoryMicroagents } from "#/hooks/query/use-repository-microagents";
import { LoadingSpinner } from "#/components/shared/loading-spinner";

export interface RepoMicroagent {
  id: string;
  repositoryName: string;
  repositoryUrl: string;
}

interface MicroagentManagementRepoMicroagentsProps {
  repoMicroagent: RepoMicroagent;
}

export function MicroagentManagementRepoMicroagents({
  repoMicroagent,
}: MicroagentManagementRepoMicroagentsProps) {
  // Extract owner and repo from repositoryName (format: "owner/repo")
  const [owner, repo] = repoMicroagent.repositoryName.split("/");

  const {
    data: microagents,
    isLoading,
    isError,
  } = useRepositoryMicroagents(owner, repo);

  if (isLoading) {
    return (
      <div className="pb-4 flex justify-center">
        <LoadingSpinner size="small" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="pb-4">
        <MicroagentManagementLearnThisRepo
          repositoryUrl={repoMicroagent.repositoryUrl}
        />
      </div>
    );
  }

  const numberOfMicroagents = microagents?.length || 0;

  return (
    <div className="pb-4">
      {numberOfMicroagents === 0 && (
        <MicroagentManagementLearnThisRepo
          repositoryUrl={repoMicroagent.repositoryUrl}
        />
      )}
      {numberOfMicroagents > 0 &&
        microagents?.map((microagent) => (
          <div key={microagent.name} className="pb-4 last:pb-0">
            <MicroagentManagementMicroagentCard
              microagent={{
                id: microagent.name,
                name: microagent.name,
                createdAt: microagent.created_at,
              }}
            />
          </div>
        ))}
    </div>
  );
}
