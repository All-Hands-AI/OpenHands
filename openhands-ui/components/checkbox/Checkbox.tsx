import { useId } from "react";
import type { HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { Typography } from "../typography/Typography";
import { Icon } from "../icon/Icon";

export type CheckboxProps = HTMLProps<"input"> & {
  label: React.ReactNode;
  labelClassName?: string;
};

export const Checkbox = ({
  className,
  label,
  labelClassName,
  id: propId,
  disabled,
  checked,
  onChange,
  ...props
}: CheckboxProps) => {
  const generatedId = useId();
  const id = propId ?? generatedId;
  return (
    <label
      htmlFor={id}
      className={cn(
        "flex items-center gap-2 cursor-pointer",
        disabled && "cursor-not-allowed"
      )}
    >
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
          "group",
          "w-5 h-5 border-1 border-grey-985 rounded-sm transition",
          "flex items-center justify-center",
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
      >
        {checked && (
          <Icon icon="CheckLg" className={cn("text-primary-500 w-6 h-6")} />
        )}
      </div>
      <Typography.Text
        fontSize="xxs"
        fontWeight={500}
        className={cn(labelClassName, disabled && "opacity-50")}
      >
        {label}
      </Typography.Text>
    </label>
  );
};
