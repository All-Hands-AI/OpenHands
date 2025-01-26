import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export type Suggestion = { label: I18nKey | string; value: string };

interface SuggestionItemProps {
  suggestion: Suggestion;
  onClick: (value: string) => void;
}

export function SuggestionItem({ suggestion, onClick }: SuggestionItemProps) {
  const { t } = useTranslation();
  return (
    <li className="list-none border border-neutral-600 rounded-xl hover:bg-neutral-700 flex-1">
      <button
        type="button"
        data-testid="suggestion"
        onClick={() => onClick(suggestion.value)}
        className="text-[16px] leading-6 -tracking-[0.01em] text-center w-full p-3 font-semibold"
      >
        {t(suggestion.label)}
      </button>
    </li>
  );
}
