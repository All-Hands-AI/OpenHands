import NewProjectIcon from "#/icons/new-project.svg?react";
import { TooltipButton } from "./tooltip-button";
import { useEndSession } from "#/hooks/use-end-session";

export function ExitProjectButton() {
  const endSession = useEndSession();

  return (
    <TooltipButton
      tooltip="Start new project"
      ariaLabel="Start new project"
      onClick={endSession}
      testId="new-project-button"
    >
      <NewProjectIcon width={28} height={28} />
    </TooltipButton>
  );
}
