interface ConversationRepoLinkProps {
  selectedRepository: string;
  onClick?: (event: React.MouseEvent<HTMLAnchorElement>) => void;
}

export function ConversationRepoLink({
  selectedRepository,
  onClick,
}: ConversationRepoLinkProps) {
  return (
    <a
      data-testid="conversation-card-selected-repository"
      href={`https://github.com/${selectedRepository}`}
      target="_blank noopener noreferrer"
      onClick={onClick}
      className="text-xs text-neutral-400 hover:text-neutral-200"
    >
      {selectedRepository}
    </a>
  );
}
