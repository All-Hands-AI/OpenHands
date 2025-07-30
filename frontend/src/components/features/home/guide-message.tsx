import { useTranslation } from "react-i18next";

export function GuideMessage() {
  const { t } = useTranslation();

  return (
    <div className="w-full flex items-center justify-center">
      <div className="w-fit flex items-center justify-center gap-1 px-[15px] rounded-[12px] bg-[#454545] leading-5 text-white text-[15px] font-normal h-[38px]">
        <span className="">{t("HOME$GUIDE_MESSAGE_TITLE")} </span>
        <a
          href="https://docs.all-hands.dev/usage/getting-started"
          target="_blank"
          rel="noopener noreferrer"
        >
          <span className="underline">{t("COMMON$CLICK_HERE")}</span>
        </a>
      </div>
    </div>
  );
}
