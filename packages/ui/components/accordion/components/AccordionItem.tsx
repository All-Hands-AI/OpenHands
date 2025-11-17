import type { PropsWithChildren } from "react";
import type { BaseProps, HTMLProps } from "../../../shared/types";
import { cn } from "../../../shared/utils/cn";
import { type IconProps } from "../../icon/Icon";
import { AccordionHeader } from "./AccordionHeader";
import { AccordionPanel } from "./AccordionPanel";

export type AccordionItemProps = HTMLProps<"div"> & {
  icon: IconProps["icon"];
  expanded: boolean;
  value: string;
  label: React.ReactNode;
  onExpandedChange(value: boolean): void;
} & BaseProps;
export type AccordionItemPropsPublic = Omit<
  AccordionItemProps,
  "expanded" | "onExpandedChange" | "className" | "style" | "testId"
>;

export const AccordionItem = ({
  className,
  children,
  expanded,
  icon,
  label,
  onExpandedChange,
  ...props
}: PropsWithChildren<AccordionItemProps>) => {
  return (
    <div {...props} className={cn("w-full", className)}>
      <AccordionHeader
        icon={icon}
        expanded={expanded}
        onClick={() => onExpandedChange(!expanded)}
      >
        {label}
      </AccordionHeader>
      <AccordionPanel expanded={expanded}>{children}</AccordionPanel>
    </div>
  );
};
