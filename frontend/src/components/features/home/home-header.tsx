import { useTranslation } from "react-i18next";
import { GuideMessage } from "./guide-message";

export function HomeHeader() {
  const { t } = useTranslation();

  return (
    <header className="flex flex-col items-center">
      <GuideMessage />
      <div className="mt-12 flex flex-col gap-4 items-center">
        <div className="h-[80px] flex items-center">
          <span className="text-[32px] text-white font-bold leading-5">
            {t("HOME$LETS_START_BUILDING")}
          </span>
        </div>
      </div>
    </header>
  );
}
