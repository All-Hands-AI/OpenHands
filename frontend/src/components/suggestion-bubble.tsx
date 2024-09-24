import Lightbulb from "#/assets/lightbulb.svg?react";
import Refresh from "#/assets/refresh.svg?react";

interface SuggestionBubbleProps {
  suggestion: string;
  onClick: () => void;
  onRefresh: () => void;
}

export function SuggestionBubble({
  suggestion,
  onClick,
  onRefresh,
}: SuggestionBubbleProps) {
  return (
    <div className="flex flex-col items-end gap-1">
      <button type="button" onClick={onRefresh} className="flex gap-1">
        <Refresh width={8} height={8} />
        <span className="text-[6px]">Refresh</span>
      </button>

      <button
        type="button"
        onClick={onClick}
        className="border border-neutral-600 rounded-lg px-[10px] py-2 flex items-center justify-center gap-2"
      >
        <Lightbulb width={18} height={18} />
        <span className="text-sm">{suggestion}</span>
      </button>
    </div>
  );
}
