import React, { useCallback, type PropsWithChildren } from "react";

import {
  AccordionItem,
  type AccordionItemPropsPublic,
} from "./components/AccordionItem";
import { cn } from "../../shared/utils/cn";
import type { HTMLProps } from "../../shared/types";

export type AccordionProps = HTMLProps<"div"> & {
  expandedKeys: string[];
  type?: "multi" | "single";
  setExpandedKeys(keys: string[]): void;
};

type AccordionType = React.FC<PropsWithChildren<AccordionProps>> & {
  Item: React.FC<PropsWithChildren<AccordionItemPropsPublic>>;
};

const Accordion: AccordionType = ({
  className,
  expandedKeys,
  setExpandedKeys,
  children,
  type = "multi",
  ...props
}) => {
  const onChange = useCallback(
    (key: string, expanded: boolean) => {
      if (type === "multi") {
        setExpandedKeys(
          expanded
            ? [...expandedKeys, key]
            : [...expandedKeys].filter((k) => k !== key)
        );
      } else {
        setExpandedKeys(expanded ? [key] : []);
      }
    },
    [expandedKeys, type]
  );

  const reactChildren = React.Children.toArray(children);
  const items =
    React.Children.map(reactChildren, (child: any) => {
      const value = child.props.value;
      const expanded = expandedKeys.some((key) => key === value);
      return React.cloneElement(child, {
        expanded,
        onExpandedChange: () => onChange(value, !expanded),
        className: "flex-1",
      });
    }) ?? [];
  return (
    <div
      className={cn("flex flex-col gap-y-2.5 items-start", className)}
      {...props}
    >
      {items}
    </div>
  );
};

Accordion.Item = AccordionItem as React.FC<
  PropsWithChildren<AccordionItemPropsPublic>
>;
export { Accordion };
