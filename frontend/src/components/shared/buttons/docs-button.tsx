import { useTranslation } from "react-i18next";
import DocsIcon from "#/icons/docs.svg?react";
import { I18nKey } from "#/i18n/declaration";
import { TooltipButton } from "./tooltip-button";

export function DocsButton() {
  const { t } = useTranslation();
  return (
    <TooltipButton
      tooltip={t(I18nKey.SIDEBAR$DOCS)}
      ariaLabel={t(I18nKey.SIDEBAR$DOCS)}
      href="https://docs.all-hands.dev"
    >
      <DocsIcon width={28} height={28} />
    </TooltipButton>
  );
}
