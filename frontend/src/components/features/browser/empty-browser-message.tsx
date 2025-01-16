import { useTranslation } from "react-i18next";
import { IoIosGlobe } from "react-icons/io";
import { I18nKey } from "#/i18n/declaration";

export function EmptyBrowserMessage() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center h-full justify-center">
      <IoIosGlobe size={100} />
      {t(I18nKey.BROWSER$EMPTY_MESSAGE)}
    </div>
  );
}
