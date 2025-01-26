import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import Clip from "#/icons/clip.svg?react";

export function AttachImageLabel() {
  const { t } = useTranslation();
  return (
    <div className="flex self-start items-center text-[#A3A3A3] text-xs leading-[18px] -tracking-[0.08px] cursor-pointer">
      <Clip width={16} height={16} />
      {t(I18nKey.LANDING$ATTACH_IMAGES)}
    </div>
  );
}
