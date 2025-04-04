import NoPageLoaded from "#/assets/no-page-loaded.png";
import { I18nKey } from "#/i18n/declaration";
import { Image } from "@heroui/react";
import { useTranslation } from "react-i18next";

export function EmptyBrowserMessage() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center h-full justify-center">
      <Image src={NoPageLoaded} alt="arrow" width={100} height={100} />
      {t(I18nKey.BROWSER$NO_PAGE_LOADED)}
    </div>
  );
}
