import {
  cloneElement,
  isValidElement,
  type PropsWithChildren,
  type ReactElement,
} from "react";
import type { HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { Typography } from "../typography/Typography";

import { invariant } from "../../shared/utils/invariant";
import { interactiveChipStyles, type InteractiveChipType } from "./utils";

export type InteractiveChipProps = Omit<
  HTMLProps<"div">,
  "label" | "aria-disabled" | "tabIndex"
> & {
  start?: ReactElement<HTMLProps<"svg">>;
  onStartClick?: React.MouseEventHandler<HTMLButtonElement>;
  end?: ReactElement<HTMLProps<"svg">>;
  onEndClick?: React.MouseEventHandler<HTMLButtonElement>;
  type?: InteractiveChipType;
  disabled?: boolean;
};

export const InteractiveChip = ({
  className,
  start,
  end,
  type = "elevated",
  children,
  disabled = false,
  onStartClick,
  onEndClick,
  ...props
}: PropsWithChildren<InteractiveChipProps>) => {
  invariant(typeof children === "string", "Children must be string");

  const iconCss = cn("w-4 h-4 text-inherit");
  const buttonCss = cn(disabled ? "cursor-not-allowed" : "cursor-pointer");

  const interactiveChipClassName = interactiveChipStyles[type];

  return (
    <div
      {...props}
      data-disabled={disabled ? "true" : "false"}
      aria-disabled={disabled ? "true" : "false"}
      className={cn(
        "flex flex-row items-center p-1 gap-x-1 rounded-lg",
        "active:data-[disabled=false]:scale-90 transition",
        interactiveChipClassName,
        className
      )}
    >
      {start && isValidElement(start) ? (
        <button
          tabIndex={disabled ? -1 : 0}
          onClick={onStartClick}
          className={cn(buttonCss)}
        >
          {cloneElement(start, {
            className: iconCss,
          })}
        </button>
      ) : null}
      <Typography.Text fontSize="xs" className="text-inherit">
        {children}
      </Typography.Text>

      {end && isValidElement(end) ? (
        <button
          tabIndex={disabled ? -1 : 0}
          onClick={onEndClick}
          className={cn(buttonCss)}
        >
          {cloneElement(end, {
            className: iconCss,
          })}
        </button>
      ) : null}
    </div>
  );
};
