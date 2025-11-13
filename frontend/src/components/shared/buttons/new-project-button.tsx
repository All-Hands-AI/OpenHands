import { useLocation } from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";
import PlusIcon from "#/icons/u-plus.svg?react";
import { useAuthWallet } from "#/hooks/use-auth";

interface NewProjectButtonProps {
  disabled?: boolean;
}

export function NewProjectButton({ disabled = false }: NewProjectButtonProps) {
  const { pathname } = useLocation();

  const { t } = useTranslation();

  if (!useAuthWallet().connected) return null;

  const startNewProject = t(I18nKey.CONVERSATION$START_NEW);

  return (
    <TooltipButton
      tooltip={startNewProject}
      ariaLabel={startNewProject}
      navLinkTo="/"
      testId="new-project-button"
      disabled={disabled}
    >
      <PlusIcon
        width={24}
        height={24}
        color={pathname === "/" ? "#ffffff" : "#B1B9D3"}
      />
    </TooltipButton>
  );
}
