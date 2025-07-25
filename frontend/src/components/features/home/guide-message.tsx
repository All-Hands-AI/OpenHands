import { useTranslation } from "react-i18next";
import { Typography } from "@openhands/ui";

export function GuideMessage() {
  const { t } = useTranslation();

  return (
    <div className="w-full flex items-center justify-center">
      <div className="w-fit rounded-full px-[16px] py-[15px] bg-[#575B68] leading-5">
        <Typography.Text className="text-[#D0D9FA] font-normal text-sm">
          {t("HOME$GUIDE_MESSAGE_TITLE")}{" "}
        </Typography.Text>
        <a
          href="https://docs.all-hands.dev/usage/getting-started"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Typography.Text className="text-white font-normal text-sm">
            {t("COMMON$CLICK_HERE")}
          </Typography.Text>
        </a>
      </div>
    </div>
  );
}
