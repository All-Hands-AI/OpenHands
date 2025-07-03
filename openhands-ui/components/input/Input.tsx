import {
  cloneElement,
  isValidElement,
  useId,
  type ReactElement,
  type ReactNode,
} from "react";
import type { HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { Typography } from "../typography/Typography";
import { cloneIcon } from "../../shared/utils/clone-icon";

export type InputProps = Omit<
  HTMLProps<"input">,
  "label" | "aria-invalid" | "checked"
> & {
  label: string;
  start?: ReactElement<HTMLProps<"svg">>;
  end?: ReactElement<HTMLProps<"svg">>;
  error?: string;
  hint?: string;
};

export const Input = ({
  className,
  label,
  id: propId,
  disabled,
  value,
  onChange,
  start,
  end,
  error,
  type,
  hint,
  readOnly,
  ...props
}: InputProps) => {
  const generatedId = useId();
  const id = propId ?? generatedId;

  const iconCss = cn(
    "w-6 h-6 text-light-neutral-300",
    error && " text-red-400"
  );

  return (
    <div>
      <label
        htmlFor={id}
        className={cn(
          "flex flex-col gap-y-2",
          disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer"
        )}
      >
        <Typography.Text fontSize="s" className="text-light-neutral-200">
          {label}
        </Typography.Text>
        <div
          className={cn(
            "flex flex-row items-center gap-x-2.5",
            "py-4.25 px-4",
            "border-light-neutral-500 border-1 rounded-2xl",
            // base
            "bg-light-neutral-950",
            // hover modifier
            "hover:bg-light-neutral-900",
            // focus modifier
            "focus-within:bg-light-neutral-900",
            // error state
            error && " border-red-400 bg-light-neutral-970",
            readOnly &&
              "bg-light-neutral-985 border-none hover:bg-light-neutral-985 cursor-auto",
            //  disabled modifier
            disabled && "hover:bg-light-neutral-950"
          )}
        >
          {cloneIcon(start, {
            className: iconCss,
          })}
          <input
            id={id}
            type={type}
            value={value}
            onChange={onChange}
            disabled={disabled}
            aria-invalid={error ? "true" : "false"}
            readOnly={readOnly}
            className={cn(
              "flex-1 outline-none caret-primary-500 text-white",
              "placeholder:text-light-neutral-300",
              error && "text-red-400"
            )}
            {...props}
          />
          {cloneIcon(end, {
            className: iconCss,
          })}
        </div>
        <Typography.Text
          fontSize="xs"
          className={cn("text-light-neutral-600 ml-4", error && "text-red-400")}
        >
          {error ?? hint}
        </Typography.Text>
      </label>
    </div>
  );
};
