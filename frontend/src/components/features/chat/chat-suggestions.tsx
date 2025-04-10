import { useTranslation } from "react-i18next";
import { Suggestions } from "#/components/features/suggestions/suggestions";
import { I18nKey } from "#/i18n/declaration";
import { SUGGESTIONS } from "#/utils/suggestions";
import RocketImage from "#/assets/images/rocket-image";

interface ChatSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
}

export function ChatSuggestions({ onSuggestionsClick }: ChatSuggestionsProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6 h-full px-4 items-center justify-center">
      <div className="flex flex-col items-center p-4 bg-white dark:bg-neutral-300 rounded-xl w-full gap-1">
        <RocketImage className="w-[54px] h-[54px]" />
        <span className="font-semibold text-neutral-100 dark:text-white text-[20px] leading-6 -tracking-[0.01em] gap-1">
          {t(I18nKey.LANDING$TITLE)}
        </span>
      </div>
      <Suggestions
        suggestions={Object.entries(SUGGESTIONS["non-repo"])
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
