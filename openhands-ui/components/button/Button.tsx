import type { PropsWithChildren, ReactElement } from "react";
import type { ComponentVariant, HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { invariant } from "../../shared/utils/invariant";
import { buttonStyles } from "./utils";
import { Typography } from "../typography/Typography";
import { cloneIcon } from "../../shared/utils/clone-icon";

export type ButtonProps = Omit<HTMLProps<"button">, "aria-disabled"> & {
  size?: "small" | "large";
  variant?: ComponentVariant;
  start?: ReactElement<HTMLProps<"svg">>;
  end?: ReactElement<HTMLProps<"svg">>;
};

export const Button = ({
  size = "small",
  variant = "primary",
  className,
  children,
  start,
  end,
  ...props
}: PropsWithChildren<ButtonProps>) => {
  invariant(typeof children === "string", "Children must be string");
  const buttonClassNames = buttonStyles[variant];

  const iconCss = "w-6 h-6";
  const hasIcons = start || end;

  return (
    <button
      {...props}
      aria-disabled={props.disabled ? "true" : "false"}
      className={cn(
        size === "small" ? "px-3 py-1.5 min-w-32" : "px-3 py-3 min-w-64",
        "flex flex-row items-center gap-x-8",
        hasIcons ? " justify-between" : " justify-center",
        "group enabled:cursor-pointer focus:outline-0",
        buttonClassNames.button
      )}
    >
      {cloneIcon(start, {
        className: cn(iconCss, buttonClassNames.icon),
      })}

      <Typography.Text
        fontSize="l"
        className={cn(
          "text-center font-size-l font-normal",
          buttonClassNames.text
        )}
      >
        {children}
      </Typography.Text>
      {cloneIcon(end, {
        className: cn(iconCss, buttonClassNames.icon),
      })}
    </button>
  );
};
