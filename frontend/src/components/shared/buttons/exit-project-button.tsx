import { useTranslation } from "react-i18next";
import { useLocation } from "react-router";
import { I18nKey } from "#/i18n/declaration";
import NewProjectIcon from "#/icons/new-project.svg?react";
import { TooltipButton } from "./tooltip-button";

interface ExitProjectButtonProps {
  onClick: () => void;
}

export function ExitProjectButton({ onClick }: ExitProjectButtonProps) {
  const { t } = useTranslation();
  const location = useLocation();
  const startNewProject = t(I18nKey.PROJECT$START_NEW);

  // Only show the button in the conversations page
  if (!location.pathname.startsWith("/conversations")) return null;

  return (
    <TooltipButton
      tooltip={startNewProject}
      ariaLabel={startNewProject}
      onClick={onClick}
      testId="new-project-button"
    >
      <NewProjectIcon width={26} height={26} />
    </TooltipButton>
  );
}
