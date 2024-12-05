interface NewProjectButtonProps {
  onClick: () => void;
}

export function NewProjectButton({ onClick }: NewProjectButtonProps) {
  return (
    <button
      data-testid="new-project-button"
      type="button"
      onClick={onClick}
      className="font-bold bg-[#4465DB] px-2 py-1 rounded"
    >
      + New Project
    </button>
  );
}
