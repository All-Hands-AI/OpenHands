interface ConversationRepoLinkProps {
  selectedRepository: string;
}

export function ConversationRepoLink({
  selectedRepository,
}: ConversationRepoLinkProps) {
  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    window.open(
      `https://github.com/${selectedRepository}`,
      "_blank",
      "noopener,noreferrer",
    );
  };

  return (
    <button
      type="button"
      data-testid="conversation-card-selected-repository"
      onClick={handleClick}
      className="text-xs text-neutral-400 hover:text-neutral-200"
    >
      {selectedRepository}
    </button>
  );
}
