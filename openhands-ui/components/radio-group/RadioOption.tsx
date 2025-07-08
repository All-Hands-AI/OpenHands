import { useId } from "react";
import type { HTMLProps } from "../../shared/types";
import { Typography } from "../typography/Typography";
import { cn } from "../../shared/utils/cn";

type RadioOptionProps = Omit<HTMLProps<"input">, "id" | "checked"> & {
  label: React.ReactNode;
  labelClassName?: string;
  id: string;
};

export const RadioOption = ({
  className,
  label,
  labelClassName,
  value,
  id: propId,
  disabled,
  onChange,
  ...props
}: RadioOptionProps) => {
  const generatedId = useId();
  const id = `${propId}_${generatedId}`;

  return (
    <label
      htmlFor={id}
      className={cn(
        "flex items-center gap-x-4",
        disabled ? "cursor-not-allowed" : "cursor-pointer"
      )}
    >
      <div className="relative">
        <input
          type="radio"
          id={id}
          name={propId}
          value={value}
          onChange={onChange}
          disabled={disabled}
          className="sr-only peer"
          {...props}
        />
        <div
          className={cn(
            "w-5 h-5 border-1 rounded-full transition",
            // base
            "border-light-neutral-500 bg-light-neutral-950",
            // disabled modifier
            "peer-disabled:opacity-50",
            // checked
            "peer-checked:bg-light-neutral-985",
            "peer-checked:border-primary-500",

            // hover modifier
            "peer-hover:peer-enabled:bg-light-neutral-900",
            "peer-hover:peer-enabled:border-light-neutral-200",
            "peer-hover:peer-checked:peer-enabled:bg-light-neutral-985",
            "peer-hover:peer-checked:peer-enabled:border-primary-500",

            // focus modifier
            "peer-focus:peer-enabled:bg-light-neutral-900",
            "peer-focus:peer-enabled:border-light-neutral-200",
            "peer-focus:peer-checked:peer-enabled:bg-light-neutral-985",
            "peer-focus:peer-checked:peer-enabled:border-primary-500"
          )}
        />
        <div
          className={cn(
            "absolute top-1.25 left-1.25 w-2.5 h-2.5",
            "bg-primary-500 rounded-full scale-0",
            "transition duration-200 ease-in-out",
            // checked modifier
            "peer-checked:scale-100",
            // active modifier

            "peer-active:peer-enabled:scale-80",
            "peer-active:peer-enabled:bg-primary-600"
          )}
        />
      </div>
      <Typography.Text
        fontSize="m"
        fontWeight={400}
        className={cn(labelClassName, disabled && "opacity-50")}
      >
        {label}
      </Typography.Text>
    </label>
  );
};
