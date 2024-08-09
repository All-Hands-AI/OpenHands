import React, { useEffect, useRef, useState } from "react";
import { twMerge } from "tailwind-merge";

export enum Orientation {
  HORIZONTAL = "horizontal",
  VERTICAL = "vertical",
}

type ContainerProps = {
  firstChild: React.ReactNode;
  firstClassName: string | undefined;
  secondChild: React.ReactNode;
  secondClassName: string | undefined;
  className: string | undefined;
  orientation: Orientation;
  initialSize: number;
};

export function Container({
  firstChild,
  firstClassName,
  secondChild,
  secondClassName,
  className,
  orientation,
  initialSize,
}: ContainerProps): JSX.Element {
  const [firstSize, setFirstSize] = useState<number>(initialSize);
  const [dividerPosition, setDividerPosition] = useState<number | null>(null);
  const firstRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (dividerPosition == null || !firstRef.current) {
      return undefined;
    }
    const getFirstSizeFromEvent = (e: MouseEvent) => {
      const position =
        orientation === Orientation.HORIZONTAL ? e.clientX : e.clientY;
      return firstSize + position - dividerPosition;
    };
    const onMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      const newFirstSize = getFirstSizeFromEvent(e);
      const { current } = firstRef;
      if (current) {
        if (orientation === Orientation.HORIZONTAL) {
          current.style.width = `${newFirstSize}px`;
        } else {
          current.style.height = `${newFirstSize}px`;
        }
      }
    };
    const onMouseUp = (e: MouseEvent) => {
      e.preventDefault();
      setFirstSize(getFirstSizeFromEvent(e));
      setDividerPosition(null);
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [dividerPosition, firstSize, orientation]);

  const onMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const position =
      orientation === Orientation.HORIZONTAL ? e.clientX : e.clientY;
    setDividerPosition(position);
  };

  const getStyleForFirst = () => {
    if (orientation === Orientation.HORIZONTAL) {
      return { width: `${firstSize}px` };
    }
    return { height: `${firstSize}px` };
  };

  return (
    <div
      className={twMerge(
        `flex ${orientation === Orientation.HORIZONTAL ? "" : "flex-col"}`,
        className,
      )}
    >
      <div ref={firstRef} className={firstClassName} style={getStyleForFirst()}>
        {firstChild}
      </div>
      <div
        className={`${orientation === Orientation.VERTICAL ? "cursor-ns-resize h-3" : "cursor-ew-resize w-3"} shrink-0`}
        onMouseDown={onMouseDown}
      />
      <div className={twMerge(secondClassName, "flex-1")}>{secondChild}</div>
    </div>
  );
}
