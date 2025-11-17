import { cn } from "../../../shared/utils/cn";
import { type DropdownIndicatorProps } from "react-select";
import { Icon } from "../../icon/Icon";

export const DropdownIndicator = ({
  selectProps,
  className,
}: DropdownIndicatorProps) => (
  <div className={cn("flex flex-row items-center", "py-3 px-3", className)}>
    <Icon
      className={cn(
        "h-5 w-5 text-light-neutral-300",
        selectProps.customProps.error && "text-red-400"
      )}
      icon="ChevronDown"
    />
  </div>
);
