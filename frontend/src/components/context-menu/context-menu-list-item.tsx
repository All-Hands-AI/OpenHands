import { cn } from "#/utils/utils";

interface ContextMenuListItemProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
}

export function ContextMenuListItem({
  children,
  onClick,
  disabled,
}: ContextMenuListItemProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={cn(
        "text-sm px-4 py-2 w-full text-start hover:bg-white/10 first-of-type:rounded-t-md last-of-type:rounded-b-md",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent",
      )}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
