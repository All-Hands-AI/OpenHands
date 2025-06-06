import { useTranslation } from "react-i18next";
import DocsIcon from "#/icons/academy.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";

interface DocsButtonProps {
  disabled?: boolean;
}

export function DocsButton({ disabled = false }: DocsButtonProps) {
  const { t } = useTranslation();
  return (
    <TooltipButton
      tooltip={t(I18nKey.SIDEBAR$DOCS)}
      ariaLabel={t(I18nKey.SIDEBAR$DOCS)}
      href="https://docs.all-hands.dev"
      disabled={disabled}
    >
      <DocsIcon
        width={28}
        height={28}
        className={`text-[#9099AC] ${disabled ? "opacity-50" : ""}`}
      />
    </TooltipButton>
  );
}
