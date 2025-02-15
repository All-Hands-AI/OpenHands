import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface NewConversationButtonProps {
  onClick: () => void;
}

export function NewConversationButton({ onClick }: NewConversationButtonProps) {
  const { t } = useTranslation();
  return (
    <button
      data-testid="new-conversation-button"
      type="button"
      onClick={onClick}
      className="font-bold bg-[#4465DB] px-2 py-1 rounded"
    >
      + {t(I18nKey.PROJECT$NEW)}
    </button>
  );
}
