import { type OptionProps } from "react-select";
import type { IOption } from "../../../shared/types";
import { Typography } from "../../typography/Typography";
import { cn } from "../../../shared/utils/cn";

export const Option = ({
  className,
  children,
  isSelected,
  innerProps,
  data,
  selectProps: {
    customProps: { filterOption },
    options,
    inputValue,
  },
}: OptionProps & { value: unknown }) => {
  const visibleOptions = (options ?? []).filter((o) =>
    filterOption(
      {
        // @ts-ignore
        ...o,
        data: {
          __isNew__: false,
        },
      },
      inputValue
    )
  );
  const lastOption =
    visibleOptions?.length > 0
      ? (visibleOptions![visibleOptions!.length - 1] as IOption<unknown>)
      : null;

  const option = data as IOption<unknown>;
  const isLast = option.value === lastOption?.value;
  return (
    <Typography.Text
      fontSize="m"
      fontWeight={isSelected ? 600 : 400}
      className={cn(
        className,
        "block px-6 py-3 cursor-pointer",
        "text-light-neutral-200",
        "hover:bg-blue/50 hover:font-semibold",
        isLast && "rounded-b-2xl"
      )}
      {...innerProps}
    >
      {children}
    </Typography.Text>
  );
};
