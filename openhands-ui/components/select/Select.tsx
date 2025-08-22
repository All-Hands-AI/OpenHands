import { useId, useMemo, useState } from "react";
import type { BaseProps, HTMLProps, IOption } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import ReactSelect, { createFilter } from "react-select";
import { Typography } from "../typography/Typography";
import { DropdownIndicator } from "./components/DropdownIndicator";
import { Placeholder } from "./components/Placeholder";
import { SingleValue } from "./components/SingleValue";
import { Option } from "./components/Option";

export type SelectProps<T> = Omit<HTMLProps<"input">, "value" | "onChange"> & {
  error?: string;
  hint?: string;
  label: string;
  value?: IOption<T> | null;
  options: IOption<T>[];
  noOptionsText?: string;
  onChange(value: IOption<T> | null): void;
} & BaseProps;

export const Select = <T extends string>(props: SelectProps<T>) => {
  const {
    error,
    hint,
    options,
    value,
    id: propId,
    autoFocus,
    placeholder,
    disabled,
    label,
    onChange,
    readOnly,
    noOptionsText,
    className,
    testId,
  } = props;
  const [inputValue, setInputValue] = useState("");
  const generatedId = useId();
  const id = propId ?? generatedId;

  const filterOption = useMemo(
    () =>
      createFilter({
        ignoreCase: true,
        ignoreAccents: true,
        trim: true,
        matchFrom: "any",
      }),
    []
  );

  return (
    <label
      data-testid={testId}
      htmlFor={id}
      className={cn(
        "flex flex-col gap-y-2",
        disabled ? "cursor-not-allowed opacity-50" : "cursor-pointer",
        className
      )}
    >
      <Typography.Text fontSize="s" className="text-light-neutral-200">
        {label}
      </Typography.Text>
      <ReactSelect
        inputValue={inputValue}
        value={value}
        tabSelectsValue={false}
        unstyled
        isSearchable
        backspaceRemovesValue
        autoFocus={autoFocus}
        noOptionsMessage={() => (
          <Typography.Text className="py-3 block">
            {noOptionsText ?? "No options"}
          </Typography.Text>
        )}
        isDisabled={disabled ?? readOnly}
        filterOption={filterOption}
        customProps={{ error, readOnly, hint }}
        onInputChange={(value, action) => {
          if (action.action === "input-change") {
            setInputValue(value);
            const val = props.value?.label;
            if (val != null && val !== value) {
              props.onChange(null);
            }
          }
        }}
        onChange={(option) => {
          onChange(option as IOption<T>);
          setInputValue("");
        }}
        placeholder={placeholder ?? ""}
        options={options}
        menuPortalTarget={document.body}
        classNames={{
          indicatorSeparator: (state) =>
            cn(
              "bg-light-neutral-500",
              state.selectProps.customProps.error && "bg-red-400",
              state.selectProps.customProps.readOnly && "bg-light-neutral-985"
            ),
          input: () => cn("text-white"),
          valueContainer: () => cn("py-4.25 px-4"),
          control: (state) =>
            cn(
              "border-light-neutral-500 border-1 bg-light-neutral-950",
              state.menuIsOpen ? "rounded-t-2xl" : "rounded-2xl",
              "hover:bg-light-neutral-900",
              "focus-within:bg-light-neutral-900",
              state.selectProps.customProps.error && "border-red-400",
              state.selectProps.customProps.readOnly &&
                "bg-light-neutral-985 border-none hover:bg-light-neutral-985 cursor-auto"
            ),
          menu: () =>
            cn(
              "border-light-neutral-500 border-1 border-t-0 rounded-b-2xl bg-light-neutral-950"
            ),
        }}
        components={{
          DropdownIndicator,
          Placeholder,
          // @ts-ignore
          Option: Option,
          SingleValue,
        }}
      />
      <Typography.Text
        fontSize="xs"
        className={cn("text-light-neutral-600 ml-4", error && "text-red-400")}
      >
        {error ?? hint}
      </Typography.Text>
    </label>
  );
};
