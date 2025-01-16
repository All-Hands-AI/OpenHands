import { Suggestions } from "#/components/features/suggestions/suggestions";
import BuildIt from "#/icons/build-it.svg?react";
import { SUGGESTIONS } from "#/utils/suggestions";

interface ChatSuggestionsProps {
  onSuggestionsClick: (value: string) => void;
}

export function ChatSuggestions({ onSuggestionsClick }: ChatSuggestionsProps) {
  return (
    <div className="flex flex-col gap-6 h-full px-4 items-center justify-center">
      <div className="flex flex-col items-center p-4 bg-neutral-700 rounded-xl w-full">
        <BuildIt width={45} height={54} />
        <span className="font-semibold text-[20px] leading-6 -tracking-[0.01em] gap-1">
          Let&apos;s start building!
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
