interface ConversationRepoLinkProps {
  selectedRepository: string;
}

export function ConversationRepoLink({
  selectedRepository,
}: ConversationRepoLinkProps) {
  return (
    <span
      data-testid="conversation-card-selected-repository"
      className="text-xs text-neutral-400"
    >
      {selectedRepository}
    </span>
  );
}
