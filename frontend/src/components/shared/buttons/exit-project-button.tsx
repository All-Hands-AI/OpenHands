import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import PlusIcon from "#/icons/plus.svg?react";
import PlusWhiteIcon from "#/icons/plus-white.svg?react";
import { TooltipButton } from "./tooltip-button";
import { cn } from "#/utils/utils";

interface ExitProjectButtonProps {
  onClick: () => void;
  isActive?: boolean;
}

export function ExitProjectButton({
  onClick,
  isActive = false,
}: ExitProjectButtonProps) {
  const { t } = useTranslation();
  const startNewProject = t(I18nKey.PROJECT$START_NEW);
  const Icon = isActive ? PlusWhiteIcon : PlusIcon;

  return (
    <TooltipButton
      tooltip={startNewProject}
      ariaLabel={startNewProject}
      onClick={onClick}
      testId="new-project-button"
      className={cn(
        "rounded-lg p-2 transition-colors w-10 h-10",
        "hover:bg-[#262525]",
        isActive && "bg-[#262525]",
      )}
    >
      <Icon className="transition-colors" />
    </TooltipButton>
  );
}
