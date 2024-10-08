interface ContextMenuListItemProps {
  children: React.ReactNode;
  onClick?: () => void;
}

export function ContextMenuListItem({
  children,
  onClick,
}: ContextMenuListItemProps) {
  return (
    <button
      type="button"
      className="text-sm px-4 py-2 w-full text-start hover:bg-white/10 first-of-type:rounded-t-md last-of-type:rounded-b-md"
      onClick={onClick}
    >
      {children}
    </button>
  );
}
