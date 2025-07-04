import clsx from "clsx";
import React, { useEffect, useRef, useState } from "react";
import { NavTab } from "./nav-tab";
import { ChevronLeft } from "../../assets/chevron-left";
import { ChevronRight } from "../../assets/chevron-right";

interface ContainerProps {
  label?: React.ReactNode;
  labels?: {
    label: string | React.ReactNode;
    to: string;
    icon?: React.ReactNode;
    isBeta?: boolean;
    isLoading?: boolean;
    rightContent?: React.ReactNode;
  }[];
  children: React.ReactNode;
  className?: React.HTMLAttributes<HTMLDivElement>["className"];
}

export function Container({
  label,
  labels,
  children,
  className,
}: ContainerProps) {
  const [containerWidth, setContainerWidth] = useState(0);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Track container width using ResizeObserver
  useEffect(() => {
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  // Check scroll position and update button states
  const updateScrollButtons = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } =
        scrollContainerRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth);
    }
  };

  // Update scroll buttons when tabs change or container width changes
  useEffect(() => {
    updateScrollButtons();
  }, [labels, containerWidth]);

  // Scroll functions
  const scrollLeft = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: -200, behavior: "smooth" });
    }
  };

  const scrollRight = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: 200, behavior: "smooth" });
    }
  };

  const showScrollButtons = containerWidth < 598 && labels && labels.length > 0;

  return (
    <div
      ref={containerRef}
      className={clsx(
        "bg-base-secondary border border-neutral-600 rounded-xl flex flex-col h-full w-full",
        className,
      )}
    >
      {labels && (
        <div className="relative flex items-center h-[36px] w-full">
          {/* Left scroll button */}
          {showScrollButtons && (
            <button
              type="button"
              onClick={scrollLeft}
              disabled={!canScrollLeft}
              className={clsx(
                "absolute left-0 z-10 bg-base-secondary border-r border-neutral-600 h-full px-2 flex items-center justify-center",
                "hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed",
                "rounded-tl-xl",
              )}
            >
              <ChevronLeft width={16} height={16} active={canScrollLeft} />
            </button>
          )}

          {/* Scrollable tabs container */}
          <div
            ref={scrollContainerRef}
            className={clsx(
              "flex text-xs overflow-x-auto scrollbar-hide w-full",
              showScrollButtons && "mx-8",
            )}
            onScroll={updateScrollButtons}
          >
            {labels.map(
              ({ label: l, to, icon, isBeta, isLoading, rightContent }) => (
                <NavTab
                  key={to}
                  to={to}
                  label={l}
                  icon={icon}
                  isBeta={isBeta}
                  isLoading={isLoading}
                  rightContent={rightContent}
                />
              ),
            )}
          </div>

          {/* Right scroll button */}
          {showScrollButtons && (
            <button
              type="button"
              onClick={scrollRight}
              disabled={!canScrollRight}
              className={clsx(
                "absolute right-0 z-10 bg-base-secondary border-l border-neutral-600 h-full px-2 flex items-center justify-center",
                "hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed",
                "rounded-tr-xl",
              )}
            >
              <ChevronRight width={16} height={16} active={canScrollRight} />
            </button>
          )}
        </div>
      )}
      {!labels && label && (
        <div className="px-2 h-[36px] border-b border-neutral-600 text-xs flex items-center">
          {label}
        </div>
      )}
      <div className="overflow-hidden flex-grow rounded-b-xl">{children}</div>
    </div>
  );
}
