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
  selectProps: { options, inputValue, filterOption },
}: OptionProps & { value: unknown }) => {
  // In the current design, last option (which may be really last option or last visible option if the search term is present)
  // has to be rounded.  Therefore, that calculation is applied here by using filterOption function from react-select.
  // Unfortunately, this function is meant to be applied only internally which means API of this function is not really
  // user-friendly (look at the __isNew__ property).
  // Ideally, either design will be changed or another implementation of this functionality will be explored.

  const visibleOptions = filterOption
    ? (options ?? []).filter((o) =>
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
      )
    : options;
  const lastOption = visibleOptions[
    visibleOptions!.length - 1
  ] as IOption<unknown>;

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
