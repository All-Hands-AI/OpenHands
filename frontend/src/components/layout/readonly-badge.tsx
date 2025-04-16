import { useTranslation } from "react-i18next";
import { Tooltip } from "@heroui/react";
import { I18nKey } from "#/i18n/declaration";

interface ReadonlyBadgeProps {
  showTooltip?: boolean;
}

export function ReadonlyBadge({ showTooltip = false }: ReadonlyBadgeProps) {
  const { t } = useTranslation();

  const badge = (
    <span className="text-[10px] font-medium text-white bg-neutral-600 px-2 py-0.5 rounded-md ml-1">
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
