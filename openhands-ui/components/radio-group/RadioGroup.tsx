import { useId } from "react";
import type { HTMLProps, IOption } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import { RadioOption } from "./RadioOption";

export type RadioGroupProps<T extends string> = Omit<
  HTMLProps<"input">,
  "value" | "onChange"
> & {
  options: IOption<T>[];
  value: T;
  onChange: (option: IOption<T>) => void;
  labelClassName?: string;
};

export const RadioGroup = <T extends string>({
  value,
  options,
  onChange,
  className,
  labelClassName,
  disabled,
  id: propId,
  ...props
}: RadioGroupProps<T>) => {
  const generatedId = useId();
  const id = propId ?? generatedId;

  return (
    <div className={cn("flex flex-col gap-y-1", className)}>
      {options.map((o) => (
        <RadioOption
          {...props}
          key={o.value}
          id={id}
          label={o.label}
          value={o.value}
          disabled={disabled}
          labelClassName={labelClassName}
          onChange={() => onChange(o)}
        />
      ))}
    </div>
  );
};
