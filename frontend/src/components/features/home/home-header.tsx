import { Typography } from "@openhands/ui";
import { useTranslation } from "react-i18next";
import { GuideMessage } from "./guide-message";
import YellowHand from "#/icons/yellow-hand.svg?react";

export function HomeHeader() {
  const { t } = useTranslation();

  return (
    <header className="flex flex-col items-center">
      <GuideMessage />
      <div className="mt-[95px] pt-[46px] flex flex-col gap-[27px] items-center">
        <YellowHand />
        <Typography.Text className="text-[32px] text-[#D0D9FA] font-normal">
          {t("HOME$LETS_START_BUILDING")}
        </Typography.Text>
      </div>
    </header>
  );
}
