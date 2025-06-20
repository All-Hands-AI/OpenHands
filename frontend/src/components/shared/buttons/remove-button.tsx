import { cn } from "#/utils/utils";
import CloseIcon from "#/icons/close.svg?react";

interface RemoveButtonProps {
  onClick: () => void;
  className?: React.HTMLAttributes<HTMLDivElement>["className"];
}

export function RemoveButton({ onClick, className }: RemoveButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "bg-neutral-400 rounded-full w-5 h-5 flex items-center justify-center",
        className,
      )}
    >
      <CloseIcon width={18} height={18} />
    </button>
  );
}
