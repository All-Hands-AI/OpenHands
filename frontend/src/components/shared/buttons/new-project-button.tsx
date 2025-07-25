import { useLocation } from "react-router";
import { Icon } from "@openhands/ui";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";

interface NewProjectButtonProps {
  disabled?: boolean;
}

export function NewProjectButton({ disabled = false }: NewProjectButtonProps) {
  const { pathname } = useLocation();

  const { t } = useTranslation();

  const startNewProject = t(I18nKey.CONVERSATION$START_NEW);

  return (
    <TooltipButton
      tooltip={startNewProject}
      ariaLabel={startNewProject}
      navLinkTo="/"
      testId="new-project-button"
      disabled={disabled}
    >
      <Icon
        icon="Plus"
        width={35}
        height={35}
        fill={pathname === "/" ? "#ffffff" : "#B1B9D3"}
      />
    </TooltipButton>
  );
}
