import { useTranslation } from "react-i18next";
import { GuideMessage } from "./guide-message";
import YellowHand from "#/icons/yellow-hand.svg?react";

export function HomeHeader() {
  const { t } = useTranslation();

  return (
    <header className="flex flex-col items-center">
      <GuideMessage />
      <div className="mt-5 flex flex-col gap-4 items-center">
        <YellowHand
          className="w-[77px] h-[94px]"
          data-testid="yellow-hand-icon"
        />
        <span className="text-[32px] text-white font-bold leading-5">
          {t("HOME$LETS_START_BUILDING")}
        </span>
      </div>
    </header>
  );
}
