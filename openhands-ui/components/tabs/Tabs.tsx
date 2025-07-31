import {
  useRef,
  useState,
  type PropsWithChildren,
  type ReactElement,
} from "react";
import type { BaseProps, HTMLProps } from "../../shared/types";
import { cn } from "../../shared/utils/cn";
import React from "react";
import {
  TabItem,
  type TabItemProps,
  type TabItemPropsPublic,
} from "./components/TabItem";
import { useElementOverflow } from "./hooks/use-element-overflow";
import { useElementScroll } from "./hooks/use-element-scroll";
import { TabScroller } from "./components/TabScroller";

export type TabsProps = HTMLProps<"div"> & BaseProps;

type TabsType = React.FC<PropsWithChildren<TabsProps>> & {
  Item: React.FC<PropsWithChildren<TabItemPropsPublic>>;
};

const Tabs: TabsType = ({ children, className, testId, ...props }) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const tabListRef = useRef<HTMLDivElement>(null);

  const isOverflowing = useElementOverflow({
    contentRef: tabListRef,
    containerRef,
  });
  const { canScrollLeft, canScrollRight, scrollLeft, scrollRight } =
    useElementScroll({
      containerRef,
      scrollRef: tabListRef,
    });

  const childrenArray = React.Children.toArray(children);
  const tabs =
    React.Children.map(children, (child, index: number) => {
      const isFirst = index === 0;
      const isLast = childrenArray.length - 1 === index;
      return React.cloneElement(
        child as ReactElement,
        {
          index,
          isFirst,
          isLast,
          isActive: index === activeIndex,
          onSelect: () => setActiveIndex(index),
        } as TabItemProps
      );
    }) ?? [];

  return (
    <div data-testid={testId} className={cn("w-full", className)}>
      <div className={cn("flex flex-row items-stretch")} ref={containerRef}>
        {canScrollLeft && isOverflowing && (
          <TabScroller onScroll={scrollLeft} position="left" />
        )}

        <div
          className={cn("flex", "overflow-x-auto scrollbar-none")}
          ref={tabListRef}
          role="tablist"
          aria-label="Tabs"
        >
          {tabs}
        </div>

        {canScrollRight && isOverflowing && (
          <TabScroller onScroll={scrollRight} position="right" />
        )}
      </div>

      <div
        className={cn(
          "border-1 border-t-0 rounded-b-2xl border-light-neutral-500",
          "bg-grey-970 p-4 text-light-neutral-300"
        )}
      >
        {tabs.map((child, index) => {
          if (index !== activeIndex) {
            return null;
          }
          const tabContent = (child.props as PropsWithChildren).children;
          return (
            <div key={index} role="tabpanel" aria-labelledby={`tab-${index}`}>
              {tabContent}
            </div>
          );
        })}
      </div>
    </div>
  );
};

Tabs.Item = TabItem as React.FC<PropsWithChildren<TabItemPropsPublic>>;

export { Tabs };
