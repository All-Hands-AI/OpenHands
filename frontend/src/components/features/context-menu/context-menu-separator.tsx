import { cn } from "#/utils/utils";

interface ContextMenuSeparatorProps {
  className?: string;
}

export function ContextMenuSeparator({ className }: ContextMenuSeparatorProps) {
  return <div className={cn("w-full h-[1px] bg-[#525252]", className)} />;
}
