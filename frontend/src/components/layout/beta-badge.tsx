import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function BetaBadge() {
  const { t } = useTranslation();
  return (
    <span className="text-[10px] font-medium text-white bg-neutral-600 px-2 py-0.5 rounded-md ml-1">
      {t(I18nKey.BADGE$BETA)}
    </span>
  );
}
