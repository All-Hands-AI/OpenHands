export type Suggestion = { label: string; value: string };

interface SuggestionItemProps {
  suggestion: Suggestion;
  onClick: (value: string) => void;
}

export function SuggestionItem({ suggestion, onClick }: SuggestionItemProps) {
  return (
    <li>
      <button
        type="button"
        data-testid="suggestion"
        onClick={() => onClick(suggestion.value)}
      >
        {suggestion.label}
      </button>
    </li>
  );
}
