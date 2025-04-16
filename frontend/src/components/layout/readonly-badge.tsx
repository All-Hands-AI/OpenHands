import { useTranslation } from "react-i18next";
import { Tooltip } from "@heroui/react";
import { I18nKey } from "#/i18n/declaration";

interface ReadonlyBadgeProps {
  showTooltip?: boolean;
}

export function ReadonlyBadge({ showTooltip = false }: ReadonlyBadgeProps) {
  const { t } = useTranslation();

  const badge = (
    <span className="border rounded-md px-1 py-0.5 ml-1">
      {t(I18nKey.BADGE$READONLY)}
    </span>
  );

  if (!showTooltip) {
    return badge;
  }

  return (
    <Tooltip content={t(I18nKey.TERMINAL$TOOLTIP_READ_ONLY)} closeDelay={100}>
      {badge}
    </Tooltip>
  );
}
