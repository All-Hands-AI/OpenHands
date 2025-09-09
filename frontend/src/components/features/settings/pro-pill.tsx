import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function ProPill() {
  const { t } = useTranslation();

  return (
    <span className="absolute top-0 -right-3 bg-[#3a3c45] border border-[#ffeeaa] text-[#ffeeaa] text-[8px] font-medium px-1.5 py-0.5 rounded-full whitespace-nowrap">
      {t(I18nKey.SETTINGS$PRO_PILL)}
    </span>
  );
}
