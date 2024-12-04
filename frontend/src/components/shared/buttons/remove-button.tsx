import { cn } from "#/utils/utils";
import CloseIcon from "#/icons/close.svg?react";

interface RemoveButtonProps {
  onClick: () => void;
}

export function RemoveButton({ onClick }: RemoveButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "bg-neutral-400 rounded-full w-3 h-3 flex items-center justify-center",
        "absolute right-[3px] top-[3px]",
      )}
    >
      <CloseIcon width={10} height={10} />
    </button>
  );
}
