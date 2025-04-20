import { GitRepository } from "#/types/git";

interface ConversationRepoLinkProps {
  selectedRepository: GitRepository;
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
