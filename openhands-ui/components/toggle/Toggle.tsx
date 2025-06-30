import { useId } from "react";
import type { HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { Typography } from "../typography/Typography";

export type ToggleProps = HTMLProps<"input"> & {
  label?: React.ReactNode;
  labelClassName?: string;
};

export const Toggle = ({
  className,
  labelClassName,
  label,
  id: propId,
  disabled,
  checked,
  onChange,
  ...props
}: ToggleProps) => {
  const generatedId = useId();
  const id = propId ?? generatedId;

  return (
    <label
      htmlFor={id}
      className={cn(disabled ? "cursor-not-allowed" : "cursor-pointer")}
    >
      <div className="relative">
        <input
          id={id}
          type="checkbox"
          checked={checked}
          onChange={onChange}
          disabled={disabled}
          className="sr-only peer"
          {...props}
        />
        <div
          className={cn(
            "border-1 border-light-neutral-500",
            "w-15 h-6.5 bg-grey-970 rounded-full",
            // disabled modifier
            "peer-disabled:opacity-50",
            // checked modifier
            "peer-checked:border-primary-500",
            // hover modifier
            "peer-hover:border-light-neutral-300",
            "peer-hover:peer-checked:border-primary-300"
          )}
        />
        <div
          className={cn(
            "rounded-full",
            "absolute top-0.75 left-0.75 w-5 h-5 ",
            "transition duration-300 ease-in-out",
            // base
            "bg-light-neutral-500 scale-100",
            // checked modifier
            "peer-checked:translate-x-8.5",
            "peer-checked:bg-primary-500",
            // hover modifier
            "peer-hover:peer-enabled:scale-110",
            "peer-hover:peer-enabled:bg-light-neutral-300",
            "peer-hover:peer-checked:peer-enabled:bg-primary-300",
            // focus modifier
            "peer-focus:peer-enabled:scale-110",
            "peer-focus:peer-enabled:bg-light-neutral-300",
            "peer-focus:peer-enabled:peer-checked:bg-primary-300",
            // active modifier
            "peer-active:peer-enabled:scale-80",
            "peer-active:peer-enabled:bg-light-neutral-500",
            "peer-active:peer-checked:peer-enabled:bg-primary-500",
            // disabled modifier
            "peer-disabled:opacity-50"
          )}
        />
      </div>
      {label && (
        <Typography.Text
          fontSize="xxs"
          fontWeight={500}
          className={cn(labelClassName, disabled && "opacity-50")}
        >
          {label}
        </Typography.Text>
      )}
    </label>
  );
};
