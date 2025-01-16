interface NewConversationButtonProps {
  onClick: () => void;
}

export function NewConversationButton({ onClick }: NewConversationButtonProps) {
  return (
    <button
      data-testid="new-conversation-button"
      type="button"
      onClick={onClick}
      className="font-bold bg-[#4465DB] px-2 py-1 rounded"
    >
      + New Project
    </button>
  );
}
