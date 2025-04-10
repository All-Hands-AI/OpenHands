import { cn } from "#/utils/utils"

interface ContextMenuListItemProps {
  testId?: string
  onClick: (event: React.MouseEvent<HTMLButtonElement>) => void
  isDisabled?: boolean
}

export function ContextMenuListItem({
  children,
  testId,
  onClick,
  isDisabled,
}: React.PropsWithChildren<ContextMenuListItemProps>) {
  return (
    <button
      data-testid={testId || "context-menu-list-item"}
      type="button"
      onClick={onClick}
      disabled={isDisabled}
      className={cn(
        "w-full px-4 py-2 text-start text-sm font-medium first-of-type:rounded-t-md last-of-type:rounded-b-md hover:bg-neutral-1000",
        "text-nowrap disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent",
      )}
    >
      {children}
    </button>
  )
}
