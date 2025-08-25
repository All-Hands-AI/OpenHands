import type { PropsWithChildren } from "react";
import type { BaseProps, HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";

export type ScrollableMode = "auto" | "scroll";
export type ScrollableType = "horizontal" | "vertical";

export type ScrollableProps = HTMLProps<"div"> & {
  mode?: ScrollableMode;
  type?: ScrollableType;
} & BaseProps;

const scrollableStyles: Record<
  ScrollableType,
  Record<ScrollableMode, string>
> = {
  horizontal: {
    auto: "overflow-x-auto overflow-y-hidden whitespace-nowrap",
    scroll: "overflow-x-scroll overflow-y-hidden whitespace-nowrap",
  },
  vertical: {
    auto: "overflow-y-auto overflow-x-hidden",
    scroll: "overflow-y-scroll overflow-x-hidden",
  },
};

export const Scrollable = ({
  className,
  children,
  tabIndex,
  mode = "auto",
  type = "vertical",
  testId,
  ...props
}: PropsWithChildren<ScrollableProps>) => {
  const style = scrollableStyles[type][mode];
  return (
    <div
      data-testid={testId}
      tabIndex={tabIndex ?? 0}
      {...props}
      className={cn(
        "scrollbar-thin scrollbar-thumb-light-neutral-700",
        "scrollbar-thumb-rounded-md scrollbar-track-transparent",
        style,
        className
      )}
    >
      {children}
    </div>
  );
};
