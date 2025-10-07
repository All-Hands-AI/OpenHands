import { type PropsWithChildren, type ReactElement } from "react";
import type { BaseProps, HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { cloneIcon } from "../../shared/utils/clone-icon";
import "./index.css";
import {
  buttonStyles,
  useAndApplyBoldTextWidth,
  type InteractiveChipType,
} from "./utils";

export type InteractiveChipProps = Omit<
  HTMLProps<"button">,
  "aria-disabled"
> & {
  chipType?: InteractiveChipType;
  start?: ReactElement<HTMLProps<"svg">>;
  end?: ReactElement<HTMLProps<"svg">>;
} & BaseProps;

export const InteractiveChip = ({
  chipType = "elevated",
  className,
  children,
  start,
  end,
  testId,
  ...props
}: PropsWithChildren<InteractiveChipProps>) => {
  const buttonClassNames = buttonStyles[chipType];
  const iconCss = "w-6 h-6";
  const hasIcons = start || end;
  const textRef = useAndApplyBoldTextWidth(children, "text-increase-size");

  return (
    <button
      {...props}
      data-testid={testId}
      aria-disabled={props.disabled ? "true" : "false"}
      className={cn(
        "px-1.5 py-1 min-w-32",
        "flex flex-row items-center gap-x-2",
        hasIcons ? " justify-between" : " justify-center",
        "group enabled:cursor-pointer focus:outline-0",
        buttonClassNames.button
      )}
    >
      {cloneIcon(start, {
        className: cn(iconCss, buttonClassNames.icon),
      })}

      <span
        ref={textRef}
        className={cn(
          "tg-family-outfit tg-xs text-center font-normal line-1",
          buttonClassNames.text,
          !props.disabled && `button-bold-text`
        )}
      >
        {children}
      </span>
      {cloneIcon(end, {
        className: cn(iconCss, buttonClassNames.icon),
      })}
    </button>
  );
};
