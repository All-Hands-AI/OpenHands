import { useTranslation } from "react-i18next";
import { useLocation } from "react-router";
import { I18nKey } from "#/i18n/declaration";
import PlusIcon from "#/icons/plus.svg?react";
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
      <PlusIcon width={28} height={28} className="text-[#9099AC]" />
    </TooltipButton>
  );
}
