import { useTranslation } from "react-i18next";
import { RefreshButton } from "#/components/shared/buttons/refresh-button";
import Lightbulb from "#/icons/lightbulb.svg?react";
import { I18nKey } from "#/i18n/declaration";

interface SuggestionBubbleProps {
  suggestion: { key: string; value: string };
  onClick: () => void;
  onRefresh: () => void;
}

export function SuggestionBubble({
  suggestion,
  onClick,
  onRefresh,
}: SuggestionBubbleProps) {
  const { t } = useTranslation();
  const handleRefresh = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    onRefresh();
  };

  return (
    <div
      onClick={onClick}
      className="border border-neutral-600 rounded-lg px-[10px] py-2 flex items-center justify-center gap-4 cursor-pointer"
    >
      <div className="flex items-center gap-2">
        <Lightbulb width={18} height={18} />
        <span className="text-sm">{t(suggestion.key as I18nKey)}</span>
      </div>
      <RefreshButton onClick={handleRefresh} />
    </div>
  );
}
