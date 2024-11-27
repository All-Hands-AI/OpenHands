import NewProjectIcon from "#/icons/new-project.svg?react";

interface ExitProjectButtonProps {
  onClick: () => void;
}

export function ExitProjectButton({ onClick }: ExitProjectButtonProps) {
  return (
    <button
      data-testid="new-project-button"
      type="button"
      aria-label="Start new project"
      onClick={onClick}
    >
      <NewProjectIcon width={28} height={28} />
    </button>
  );
}
