interface ContextMenuListItemProps {
  children: string;
  onClick?: () => void;
}

export function ContextMenuListItem({
  children,
  onClick,
}: ContextMenuListItemProps) {
  return (
    <li className="text-sm px-4 py-2 hover:bg-white/10 first-of-type:rounded-t-md last-of-type:rounded-b-md">
      <button type="button" onClick={onClick}>
        {children}
      </button>
    </li>
  );
}
