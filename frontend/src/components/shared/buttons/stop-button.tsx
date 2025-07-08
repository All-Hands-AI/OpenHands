import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface StopButtonProps {
  isDisabled?: boolean;
  onClick?: () => void;
}

export function StopButton({ isDisabled, onClick }: StopButtonProps) {
  const { t } = useTranslation();
  return (
    <button
      data-testid="stop-button"
      aria-label={t(I18nKey.BUTTON$STOP)}
      disabled={isDisabled}
      onClick={onClick}
      type="button"
      className="border border-white rounded-lg w-6 h-6 hover:bg-neutral-500 focus:bg-neutral-500 flex items-center justify-center cursor-pointer"
    >
      <div className="w-[10px] h-[10px] bg-white" />
    </button>
  );
}
