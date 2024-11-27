import { useTranslation } from "react-i18next";
import { VscArrowDown } from "react-icons/vsc";
import { I18nKey } from "#/i18n/declaration";

interface ScrollToBottomButtonProps {
  onClick: () => void;
}

export function ScrollToBottomButton({ onClick }: ScrollToBottomButtonProps) {
  const { t } = useTranslation();

  return (
    <button
      type="button"
      className="relative border-1 text-sm rounded px-3 py-1 border-neutral-600 bg-neutral-700 cursor-pointer select-none"
      onClick={onClick}
    >
      <span className="flex items-center">
        <VscArrowDown className="inline mr-2 w-3 h-3" />
        <span className="inline-block">
          {t(I18nKey.CHAT_INTERFACE$TO_BOTTOM)}
        </span>
      </span>
    </button>
  );
}
