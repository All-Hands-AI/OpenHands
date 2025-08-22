import { components, ControlProps, GroupBase } from "react-select";
import { SelectOption } from "./react-select-styles";

type ReactSelectCustomControlProps = ControlProps<
  SelectOption,
  false,
  GroupBase<SelectOption>
> & {
  startIcon?: React.ReactNode;
};

/* eslint-disable react/jsx-props-no-spreading */
export function ReactSelectCustomControl({
  children,
  startIcon,
  ...props
}: ReactSelectCustomControlProps) {
  return (
    <components.Control {...props}>
      {startIcon && <div>{startIcon}</div>}
      {children}
    </components.Control>
  );
}
