import { cn } from "#/utils/utils";

interface ContextMenuProps {
  children: React.ReactNode;
  className?: React.HTMLAttributes<HTMLUListElement>["className"];
}

export function ContextMenu({ children, className }: ContextMenuProps) {
  return (
    <ul className={cn("bg-[#404040] rounded-md w-[224px]", className)}>
      {children}
    </ul>
  );
}
