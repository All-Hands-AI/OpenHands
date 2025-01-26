import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function BetaBadge() {
  const { t } = useTranslation();
  return (
    <span className="text-[11px] leading-5 text-root-primary bg-neutral-400 px-1 rounded-xl">
      {t(I18nKey.BADGE$BETA)}
    </span>
  );
}
