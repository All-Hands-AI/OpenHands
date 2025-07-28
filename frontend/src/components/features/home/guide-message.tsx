import { useTranslation } from "react-i18next";

export function GuideMessage() {
  const { t } = useTranslation();

  return (
    <div className="w-full flex items-center justify-center">
      <div className="w-fit rounded-full px-[16px] py-[15px] bg-[#575B68] leading-5">
        <span className="text-[#D0D9FA] font-normal text-sm">
          {t("HOME$GUIDE_MESSAGE_TITLE")}{" "}
        </span>
        <a
          href="https://docs.all-hands.dev/usage/getting-started"
          target="_blank"
          rel="noopener noreferrer"
        >
          <span className="text-white font-normal text-sm hover:underline">
            {t("COMMON$CLICK_HERE")}
          </span>
        </a>
      </div>
    </div>
  );
}
