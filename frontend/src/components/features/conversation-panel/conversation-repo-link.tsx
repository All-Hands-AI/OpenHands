import { Repository } from "#/api/open-hands.types";

interface ConversationRepoLinkProps {
  selectedRepository: Repository;
}

export function ConversationRepoLink({
  selectedRepository,
}: ConversationRepoLinkProps) {
  const repoName = selectedRepository.full_name;
  return (
    <span
      data-testid="conversation-card-selected-repository"
      className="text-xs text-neutral-400"
    >
      {repoName}
    </span>
  );
}
