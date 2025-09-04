import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { Suggestions } from "#/components/features/suggestions/suggestions";
import { I18nKey } from "#/i18n/declaration";
import BuildIt from "#/icons/build-it.svg?react";
import { SUGGESTIONS } from "#/utils/suggestions";
import { RootState } from "#/store";
import { cn } from "#/utils/utils";

interface ChatSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
}

export function ChatSuggestions({ onSuggestionsClick }: ChatSuggestionsProps) {
  const { t } = useTranslation();
  const shouldHideSuggestions = useSelector(
    (state: RootState) => state.conversation.shouldHideSuggestions,
  );

  return (
    <div
      data-testid="chat-suggestions"
      className={cn(
        "flex flex-col h-full items-center justify-center transition-opacity duration-300 ease-in-out",
        shouldHideSuggestions ? "opacity-0 pointer-events-none" : "opacity-100",
      )}
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
