import { cn } from "#/utils/utils";

interface ContextMenuIconTextProps {
  icon: React.ComponentType<{ className?: string }>;
  text: string;
  className?: string;
  iconClassName?: string;
}

export function ContextMenuIconText({
  icon: Icon,
  text,
  className,
  iconClassName,
}: ContextMenuIconTextProps) {
  return (
    <div className={cn("flex items-center gap-3 px-1", className)}>
      <Icon className={cn("w-4 h-4 shrink-0", iconClassName)} />
      {text}
    </div>
  );
}
