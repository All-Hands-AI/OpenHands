import ChevronDoubleRight from "#/icons/chevron-double-right.svg?react";
import { cn } from "#/utils/utils";

interface ContinueButtonProps {
  onClick: () => void;
}

export function ContinueButton({ onClick }: ContinueButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "px-2 py-1 bg-neutral-700 border border-neutral-600 rounded",
        "text-[11px] leading-4 tracking-[0.01em] font-[500]",
        "flex items-center gap-2",
      )}
    >
      <ChevronDoubleRight width={12} height={12} />
      Continue
    </button>
  );
}
