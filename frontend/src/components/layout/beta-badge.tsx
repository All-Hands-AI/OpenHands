import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function BetaBadge() {
  const { t } = useTranslation();
  return (
    <span className="border rounded-md font-bold px-1 py-0.5">
      {t(I18nKey.BADGE$BETA)}
    </span>
  );
}
