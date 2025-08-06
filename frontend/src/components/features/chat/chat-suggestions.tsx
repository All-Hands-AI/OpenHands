import { useTranslation } from "react-i18next";
import { Suggestions } from "#/components/features/suggestions/suggestions";
import { I18nKey } from "#/i18n/declaration";
import BuildIt from "#/icons/build-it.svg?react";
import { SUGGESTIONS } from "#/utils/suggestions";

interface ChatSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
}

export function ChatSuggestions({ onSuggestionsClick }: ChatSuggestionsProps) {
  const { t } = useTranslation();

  return (
    <div
      data-testid="chat-suggestions"
      className="flex flex-col h-full px-4 items-center justify-center"
    >
      <div className="flex flex-col items-center p-4 rounded-xl w-full">
        <BuildIt width={86} height={103} />
        <span className="text-[32px] font-bold leading-5 text-white pt-4 pb-6">
          {t(I18nKey.LANDING$TITLE)}
        </span>
      </div>
      <Suggestions
        suggestions={Object.entries(SUGGESTIONS.repo)
          .slice(0, 4)
          .map(([label, value]) => ({
            label,
            value,
          }))}
        onSuggestionClick={onSuggestionsClick}
      />
    </div>
  );
}
