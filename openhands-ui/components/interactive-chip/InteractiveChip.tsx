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
  lead?: ReactElement<HTMLProps<"svg">>;
  onLeadClick?: React.MouseEventHandler<HTMLButtonElement>;
  trail?: ReactElement<HTMLProps<"svg">>;
  onTrailClick?: React.MouseEventHandler<HTMLButtonElement>;
  type?: InteractiveChipType;
  disabled?: boolean;
};

export const InteractiveChip = ({
  className,
  lead,
  trail,
  type = "elevated",
  children,
  disabled = false,
  onLeadClick,
  onTrailClick,
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
      {lead && isValidElement(lead) ? (
        <button
          tabIndex={disabled ? -1 : 0}
          onClick={onLeadClick}
          className={cn(buttonCss)}
        >
          {cloneElement(lead, {
            className: iconCss,
          })}
        </button>
      ) : null}
      <Typography.Text fontSize="xs" className="text-inherit">
        {children}
      </Typography.Text>

      {trail && isValidElement(trail) ? (
        <button
          tabIndex={disabled ? -1 : 0}
          onClick={onTrailClick}
          className={cn(buttonCss)}
        >
          {cloneElement(trail, {
            className: iconCss,
          })}
        </button>
      ) : null}
    </div>
  );
};
