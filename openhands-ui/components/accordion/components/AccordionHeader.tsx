import type { PropsWithChildren } from "react";
import type { HTMLProps } from "../../../shared/types";
import { cn } from "../../../shared/utils/cn";
import { Icon, type IconProps } from "../../icon/Icon";
import { Typography } from "../../typography/Typography";

export type AccordionHeaderProps = Omit<
  HTMLProps<"button">,
  "aria-disabled" | "disabled"
> & {
  icon: IconProps["icon"];
  expanded: boolean;
};

export const AccordionHeader = ({
  className,
  children,
  icon,
  expanded,
  ...props
}: PropsWithChildren<AccordionHeaderProps>) => {
  const iconCss = [
    "shrink-0 text-light-neutral-500",
    // expanded state
    "group-data-[expanded=true]:text-light-neutral-15",
    // hover modifier
    "group-hover:text-light-neutral-15",
    "group-focus:text-light-neutral-15",
  ];
  return (
    <button
      {...props}
      onBlur={() => console.log("blur")}
      data-expanded={expanded}
      className={cn(
        "px-5.5 py-3.5 min-w-32 w-full",
        "flex flex-row items-center gap-x-6 justify-between",
        "group cursor-pointer",
        // " focus:outline-0",
        "ring-1 ring-solid ring-light-neutral-500",
        expanded ? "rounded-t-2xl" : "rounded-2xl",
        "data-[expanded=true]:bg-light-neutral-900 data-[expanded=false]:bg-grey-800",
        // hover modifier
        "data-[expanded=true]:hover:bg-light-neutral-900",
        // focus modifier
        "data-[expanded=false]:focus:bg-light-neutral-900"
      )}
    >
      <Icon icon={icon} className={cn(iconCss, "w-6 h-6")} />

      <Typography.Text
        fontSize="m"
        fontWeight={500}
        className={cn(
          "flex-1 text-left truncate",
          "text-light-neutral-500",
          // expanded state
          "group-data-[expanded=true]:text-light-neutral-15",
          // hover modifier
          "group-hover:text-light-neutral-15",
          // focus modifier
          "group-focus:text-light-neutral-15"
        )}
      >
        {children}
      </Typography.Text>
      <Icon
        icon={"ChevronUp"}
        className={cn(
          iconCss,
          "h-4 w-4",
          "transition-transform duration-300",
          expanded && `rotate-180`
        )}
      />
    </button>
  );
};
