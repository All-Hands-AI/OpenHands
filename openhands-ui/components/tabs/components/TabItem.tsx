import type { HTMLProps } from "../../../shared/types";
import { cn } from "../../../shared/utils/cn";
import React from "react";
import { Icon, type IconProps } from "../../icon/Icon";
import { Typography } from "../../typography/Typography";

export type TabItemProps = HTMLProps<"div"> & {
  icon?: IconProps["icon"];
  text: string;
  children: React.ReactNode;
  index: number;
  isActive: boolean;
  isFirst: boolean;
  isLast: boolean;
  onSelect: () => void;
};
export type TabItemPropsPublic = Omit<
  TabItemProps,
  "index" | "isActive" | "isFirst" | "isLast" | "onSelect"
>;

export const TabItem = ({
  text,
  index,
  isActive,
  isFirst,
  isLast,
  onSelect,
  icon,
}: TabItemProps) => {
  return (
    <button
      role="tab"
      id={`tab-${index}`}
      aria-selected={isActive}
      aria-controls={`panel-${index}`}
      className={cn(
        "flex items-center gap-x-3 cursor-pointer",
        "px-6 py-3",
        "text-light-neutral-15 whitespace-nowrap",
        "border-light-neutral-500 border-b-1 border-t-1 border-r-1",
        "bg-light-neutral-970 focus:outline-0",
        "enabled:hover:bg-light-neutral-500",
        "enabled:focus:bg-grey-970",
        "enabled:active:bg-grey-970 enabled:active:text-primary-500",
        isActive && "enabled:text-primary-500",
        isFirst && "border-l-1 rounded-tl-2xl",
        isLast && "rounded-tr-2xl"
      )}
      onClick={onSelect}
    >
      {icon && <Icon icon={icon} className={cn("w-4 h-4 shrink-0")} />}
      <Typography.Text fontSize={"s"} fontWeight={400}>
        {text}
      </Typography.Text>
    </button>
  );
};
