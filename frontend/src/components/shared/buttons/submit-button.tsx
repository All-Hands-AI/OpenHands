import { useTranslation } from "react-i18next";
import ArrowSendIcon from "#/icons/arrow-send.svg?react";
import { I18nKey } from "#/i18n/declaration";

interface SubmitButtonProps {
  isDisabled?: boolean;
  onClick: () => void;
}

export function SubmitButton({ isDisabled, onClick }: SubmitButtonProps) {
  const { t } = useTranslation();
  return (
    <button
      aria-label={t(I18nKey.BUTTON$SEND)}
      disabled={isDisabled}
      onClick={onClick}
      type="submit"
      className="rounded-lg bg-[#dedede] hover:bg-[#ececec] w-10 h-10 flex items-center justify-center"
    >
      <ArrowSendIcon />
    </button>
  );
}
