import Lightbulb from "#/icons/lightbulb.svg?react";
import Refresh from "#/icons/refresh.svg?react";

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
    <div
      onClick={onClick}
      className="border border-neutral-600 rounded-lg px-[10px] py-2 flex items-center justify-center gap-4 cursor-pointer"
    >
      <div className="flex items-center gap-2">
        <Lightbulb width={18} height={18} />
        <span className="text-sm">{suggestion}</span>
      </div>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onRefresh();
        }}
      >
        <Refresh width={14} height={14} />
      </button>
    </div>
  );
}
