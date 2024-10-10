import { cn } from "#/utils/utils";

interface BoldProps {
  underline?: boolean;
}

export function Bold({
  children,
  underline,
}: React.PropsWithChildren<BoldProps>) {
  return <strong className={cn(underline && "underline")}>{children}</strong>;
}
