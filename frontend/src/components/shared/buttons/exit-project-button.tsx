import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import NewProjectIcon from "#/icons/new-project.svg?react";
import { TooltipButton } from "./tooltip-button";

interface ExitProjectButtonProps {
  onClick: () => void;
}

export function ExitProjectButton({ onClick }: ExitProjectButtonProps) {
  const { t } = useTranslation();
  const startNewProject = t(I18nKey.PROJECT$START_NEW);
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
