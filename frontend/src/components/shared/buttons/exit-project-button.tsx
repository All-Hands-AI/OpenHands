import NewProjectIcon from "#/icons/new-project.svg?react";
import { TooltipButton } from "./tooltip-button";

interface ExitProjectButtonProps {
  onClick: () => void;
}

export function ExitProjectButton({ onClick }: ExitProjectButtonProps) {
  return (
    <TooltipButton
      tooltip="Start new project"
      ariaLabel="Start new project"
      onClick={onClick}
      testId="new-project-button"
    >
      <NewProjectIcon width={26} height={26} />
    </TooltipButton>
  );
}
