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
  const [firstSize, setFirstSize] = useState<number | undefined>(initialSize);
  const [dividerPosition, setDividerPosition] = useState<undefined | number>(
    undefined,
  );
  const firstRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (firstRef.current !== null) {
      if (orientation === Orientation.HORIZONTAL) {
        firstRef.current.style.width = `${firstSize}px`;
      } else {
        firstRef.current.style.height = `${firstSize}px`;
      }
    }
  }, [firstSize, orientation]);

  const onMouseMove = (e: MouseEvent) => {
    e.preventDefault();
    if (firstSize && dividerPosition) {
      if (orientation === Orientation.HORIZONTAL) {
        const newLeftWidth = firstSize + e.clientX - dividerPosition;
        setDividerPosition(e.clientX);
        setFirstSize(newLeftWidth);
      } else {
        const newTopHeight = firstSize + e.clientY - dividerPosition;
        setDividerPosition(e.clientY);
        setFirstSize(newTopHeight);
      }
    }
  };

  const onMouseUp = () => {
    document.removeEventListener("mousemove", onMouseMove);
    document.removeEventListener("mouseup", onMouseUp);
  };

  const onMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setDividerPosition(
      orientation === Orientation.HORIZONTAL ? e.clientX : e.clientY,
    );
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
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
