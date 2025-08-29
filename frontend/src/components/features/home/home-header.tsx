import { useTranslation } from "react-i18next";
import { GuideMessage } from "./guide-message";
import { WavingHand } from "./waving-hand";

export function HomeHeader() {
  const { t } = useTranslation();

  return (
    <header className="flex flex-col items-center">
      <GuideMessage />
      <div className="mt-5 flex flex-col gap-4 items-center">
        <WavingHand />
        <span className="text-[32px] text-white font-bold leading-5">
          {t("HOME$LETS_START_BUILDING")}
        </span>
      </div>
    </header>
  );
}
