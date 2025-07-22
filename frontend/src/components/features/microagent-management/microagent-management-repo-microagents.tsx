import { MicroagentManagementMicroagentCard } from "./microagent-management-microagent-card";
import { MicroagentManagementLearnThisRepo } from "./microagent-management-learn-this-repo";
import { useRepositoryMicroagents } from "#/hooks/query/use-repository-microagents";
import { useSearchConversations } from "#/hooks/query/use-search-conversations";
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
    isLoading: isLoadingMicroagents,
    isError: isErrorMicroagents,
  } = useRepositoryMicroagents(owner, repo);

  const {
    data: conversations,
    isLoading: isLoadingConversations,
    isError: isErrorConversations,
  } = useSearchConversations(
    repoMicroagent.repositoryName,
    "microagent_management",
    1000,
  );

  // Show loading only when both queries are loading
  const isLoading = isLoadingMicroagents || isLoadingConversations;

  // Show error UI.
  const isError = isErrorMicroagents || isErrorConversations;

  if (isLoading) {
    return (
      <div className="pb-4 flex justify-center">
        <LoadingSpinner size="small" />
      </div>
    );
  }

  // If there's an error with microagents, show the learn this repo component
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
  const numberOfConversations = conversations?.length || 0;
  const totalItems = numberOfMicroagents + numberOfConversations;

  return (
    <div className="pb-4">
      {totalItems === 0 && (
        <MicroagentManagementLearnThisRepo
          repositoryUrl={repoMicroagent.repositoryUrl}
        />
      )}

      {/* Render microagents */}
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

      {/* Render conversations */}
      {numberOfConversations > 0 &&
        conversations?.map((conversation) => (
          <div key={conversation.conversation_id} className="pb-4 last:pb-0">
            <MicroagentManagementMicroagentCard
              microagent={{
                id: conversation.conversation_id,
                name: conversation.title,
                createdAt: conversation.created_at,
                conversationStatus: conversation.status,
                runtimeStatus: conversation.runtime_status || undefined,
                prNumber: conversation.pr_number || undefined,
              }}
              showMicroagentFilePath={false}
            />
          </div>
        ))}
    </div>
  );
}
