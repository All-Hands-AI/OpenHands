import { cn } from "#/utils/utils";

interface ContextMenuListItemProps {
  onClick: () => void;
  isDisabled?: boolean;
}

export function ContextMenuListItem({
  children,
  onClick,
  isDisabled,
}: React.PropsWithChildren<ContextMenuListItemProps>) {
  return (
    <button
      data-testid="context-menu-list-item"
      type="button"
      onClick={onClick}
      disabled={isDisabled}
      className={cn(
        "text-sm px-4 py-2 w-full text-start hover:bg-white/10 first-of-type:rounded-t-md last-of-type:rounded-b-md",
        "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent",
      )}
    >
      {children}
    </button>
  );
}
