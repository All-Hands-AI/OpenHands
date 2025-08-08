import clsx from "clsx";
import { ChevronRight } from "../../assets/chevron-right";

interface ScrollRightButtonProps {
  scrollRight: () => void;
  canScrollRight: boolean;
}

export function ScrollRightButton({
  scrollRight,
  canScrollRight,
}: ScrollRightButtonProps) {
  return (
    <button
      type="button"
      onClick={scrollRight}
      disabled={!canScrollRight}
      className={clsx(
        "cursor-pointer absolute right-0 z-10 bg-base-secondary border-l border-neutral-600 h-full px-2 flex items-center justify-center",
        "hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed",
        "rounded-tr-xl",
      )}
    >
      <ChevronRight width={16} height={16} active={canScrollRight} />
    </button>
  );
}
