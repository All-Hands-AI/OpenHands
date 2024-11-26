export type Suggestion = { label: string; value: string };

interface SuggestionItemProps {
  suggestion: Suggestion;
  onClick: (value: string) => void;
}

export function SuggestionItem({ suggestion, onClick }: SuggestionItemProps) {
  return (
    <li className="list-none border border-neutral-600 rounded-xl hover:bg-neutral-700 flex-1">
      <button
        type="button"
        data-testid="suggestion"
        onClick={() => onClick(suggestion.value)}
        className="text-[16px] leading-6 -tracking-[0.01em] text-center w-full p-3 font-semibold"
      >
        {suggestion.label}
      </button>
    </li>
  );
}
