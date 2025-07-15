import clsx from "clsx";
import { ChevronLeft } from "../../assets/chevron-left";

interface ScrollLeftButtonProps {
  scrollLeft: () => void;
  canScrollLeft: boolean;
}

export function ScrollLeftButton({
  scrollLeft,
  canScrollLeft,
}: ScrollLeftButtonProps) {
  return (
    <button
      type="button"
      onClick={scrollLeft}
      disabled={!canScrollLeft}
      className={clsx(
        "cursor-pointer absolute left-0 z-10 bg-base-secondary border-r border-neutral-600 h-full px-2 flex items-center justify-center",
        "hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed",
        "rounded-tl-xl",
      )}
    >
      <ChevronLeft width={16} height={16} active={canScrollLeft} />
    </button>
  );
}
