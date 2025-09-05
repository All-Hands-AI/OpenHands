import { useTranslation } from "react-i18next";

export function HomeHeaderTitle() {
  const { t } = useTranslation();

  return (
    <div className="mt-12 flex flex-col gap-4 items-center">
      <div className="h-[80px] flex items-center">
        <span className="text-[32px] text-white font-bold leading-5">
          {t("HOME$LETS_START_BUILDING")}
        </span>
      </div>
    </div>
  );
}
