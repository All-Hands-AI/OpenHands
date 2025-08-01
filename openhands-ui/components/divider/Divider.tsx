import type { BaseProps, HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";

export type DividerProps = Omit<
  HTMLProps<"div">,
  "role" | "aria-orientation"
> & {
  type?: "horizontal" | "vertical";
} & BaseProps;

export const Divider = ({
  type = "horizontal",
  className,
  testId,
  ...props
}: DividerProps) => {
  return (
    <div
      {...props}
      className={cn(
        "bg-grey-900",
        type === "vertical" ? "w-px h-full" : "h-px w-full",
        className
      )}
      role="separator"
      aria-orientation={type}
      data-testid={testId}
    />
  );
};
