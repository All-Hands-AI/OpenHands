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
  const [currentSize, setCurrentSize] = useState<number>(initialSize);
  const [mouseDownPosition, setMouseDownPosition] = useState<number | null>(
    null,
  );
  const firstRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (mouseDownPosition == null || !firstRef.current) {
      return undefined;
    }
    const getCurrentSize = (e: MouseEvent) => {
      const position =
        orientation === Orientation.HORIZONTAL ? e.clientX : e.clientY;
      return currentSize + position - mouseDownPosition;
    };
    const onMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      const firstSize = getCurrentSize(e);
      const { current } = firstRef;
      if (current) {
        if (orientation === Orientation.HORIZONTAL) {
          current.style.width = `${firstSize}px`;
        } else {
          current.style.height = `${firstSize}px`;
        }
      }
    };
    const onMouseUp = (e: MouseEvent) => {
      e.preventDefault();
      setCurrentSize(getCurrentSize(e));
      setMouseDownPosition(null);
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [mouseDownPosition, currentSize, orientation]);

  const onMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const position =
      orientation === Orientation.HORIZONTAL ? e.clientX : e.clientY;
    setMouseDownPosition(position);
  };

  return (
    <div
      className={twMerge(
        `flex ${orientation === Orientation.HORIZONTAL ? "" : "flex-col"}`,
        className,
      )}
    >
      <div ref={firstRef} className={firstClassName}>
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
