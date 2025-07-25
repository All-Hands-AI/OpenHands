import {
  useEffect,
  useRef,
  type PropsWithChildren,
  type ReactElement,
} from "react";
import type {
  BaseProps,
  ComponentVariant,
  HTMLProps,
} from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { buttonStyles, useAndApplyBoldTextWidth } from "./utils";
import { cloneIcon } from "../../shared/utils/clone-icon";
import "./index.css";

export type ButtonProps = Omit<HTMLProps<"button">, "aria-disabled"> & {
  size?: "small" | "large";
  variant?: ComponentVariant;
  start?: ReactElement<HTMLProps<"svg">>;
  end?: ReactElement<HTMLProps<"svg">>;
} & BaseProps;

export const Button = ({
  size = "small",
  variant = "primary",
  className,
  children,
  start,
  end,
  testId,
  ...props
}: PropsWithChildren<ButtonProps>) => {
  const buttonClassNames = buttonStyles[variant];
  const iconCss = "w-6 h-6";
  const hasIcons = start || end;
  const textRef = useAndApplyBoldTextWidth(children, "text-increase-size");

  return (
    <button
      {...props}
      aria-disabled={props.disabled ? "true" : "false"}
      data-testid={testId}
      className={cn(
        size === "small" ? "px-2 py-3 min-w-32" : "px-3 py-4 min-w-64",
        "flex flex-row items-center gap-x-8",
        hasIcons ? " justify-between" : " justify-center",
        "group enabled:cursor-pointer focus:outline-0",
        buttonClassNames.button,
        className
      )}
    >
      {cloneIcon(start, {
        className: cn(iconCss, buttonClassNames.icon),
      })}

      <span
        ref={textRef}
        className={cn(
          "tg-family-outfit tg-lg text-center font-normal leading-[100%]",
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
