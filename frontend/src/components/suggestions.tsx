import { SuggestionItem, type Suggestion } from "./suggestion-item";

interface SuggestionsProps {
  suggestions: Suggestion[];
  onSuggestionClick: (value: string) => void;
}

export function Suggestions({
  suggestions,
  onSuggestionClick,
}: SuggestionsProps) {
  return (
    <ul>
      {suggestions.map((suggestion, index) => (
        <SuggestionItem
          key={index}
          suggestion={suggestion}
          onClick={onSuggestionClick}
        />
      ))}
    </ul>
  );
}
