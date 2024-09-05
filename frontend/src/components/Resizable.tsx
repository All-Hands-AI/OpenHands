import React, { CSSProperties, useEffect, useRef, useState } from "react";
import {
  VscChevronDown,
  VscChevronLeft,
  VscChevronRight,
  VscChevronUp,
} from "react-icons/vsc";
import { twMerge } from "tailwind-merge";
import IconButton from "./IconButton";

export enum Orientation {
  HORIZONTAL = "horizontal",
  VERTICAL = "vertical",
}

enum Collapse {
  COLLAPSED = "collapsed",
  SPLIT = "split",
  FILLED = "filled",
}

type ContainerProps = {
  firstChild: React.ReactNode;
  firstClassName: string | undefined;
  secondChild: React.ReactNode;
  secondClassName: string | undefined;
  className: string | undefined;
  orientation: Orientation;
};

export function Container({
  firstChild,
  firstClassName,
  secondChild,
  secondClassName,
  className,
  orientation,
}: ContainerProps): JSX.Element {
  const [dividerPosition, setDividerPosition] = useState<number | null>(null);
  const firstRef = useRef<HTMLDivElement>(null);
  const secondRef = useRef<HTMLDivElement>(null);
  const [collapse, setCollapse] = useState<Collapse>(Collapse.SPLIT);
  const isHorizontal = orientation === Orientation.HORIZONTAL;

  useEffect(() => {
    if (dividerPosition == null || !firstRef.current) {
      return undefined;
    }

    const onMouseUp = (e: MouseEvent) => {
      e.preventDefault();
      if (firstRef.current) {
        firstRef.current.style.transition = "";
      }
      if (secondRef.current) {
        secondRef.current.style.transition = "";
      }
      setDividerPosition(null);
      document.removeEventListener("mouseup", onMouseUp);
    };
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [dividerPosition, orientation]);

  const onMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    if (firstRef.current) {
      firstRef.current.style.transition = "none";
    }
    if (secondRef.current) {
      secondRef.current.style.transition = "none";
    }
    const position = isHorizontal ? e.clientX : e.clientY;
    setDividerPosition(position);
  };

  const getStyleForFirst = () => {
    const style: CSSProperties = { overflow: "hidden" };
    if (collapse === Collapse.COLLAPSED) {
      style.opacity = 0;
      style.width = 0;
      style.minWidth = 0;
      style.height = 0;
      style.minHeight = 0;
    } else {
      style.flexGrow = 1;
    }
    return style;
  };

  const getStyleForSecond = () => {
    const style: CSSProperties = { overflow: "hidden" };
    if (collapse === Collapse.FILLED) {
      style.opacity = 0;
      style.width = 0;
      style.minWidth = 0;
      style.height = 0;
      style.minHeight = 0;
    } else if (collapse === Collapse.SPLIT) {
      style.flexGrow = 1;
    } else {
      style.flexGrow = 1;
    }
    return style;
  };

  const onCollapse = () => {
    if (collapse === Collapse.SPLIT) {
      setCollapse(Collapse.COLLAPSED);
    } else {
      setCollapse(Collapse.SPLIT);
    }
  };

  const onExpand = () => {
    if (collapse === Collapse.SPLIT) {
      setCollapse(Collapse.FILLED);
    } else {
      setCollapse(Collapse.SPLIT);
    }
  };

  return (
    <div className={twMerge("flex", !isHorizontal && "flex-col", className)}>
      <div
        ref={firstRef}
        className={twMerge(firstClassName, "transition-all ease-soft-spring")}
        style={getStyleForFirst()}
      >
        {firstChild}
      </div>
      <div
        className={`${isHorizontal ? "cursor-ew-resize w-3 flex-col" : "cursor-ns-resize h-3 flex-row"} shrink-0 flex justify-center items-center`}
        onMouseDown={collapse === Collapse.SPLIT ? onMouseDown : undefined}
      >
        <IconButton
          icon={isHorizontal ? <VscChevronLeft /> : <VscChevronUp />}
          ariaLabel="Collapse"
          onClick={onCollapse}
        />
        <IconButton
          icon={isHorizontal ? <VscChevronRight /> : <VscChevronDown />}
          ariaLabel="Expand"
          onClick={onExpand}
        />
      </div>
      <div
        ref={secondRef}
        className={twMerge(secondClassName, "transition-all ease-soft-spring")}
        style={getStyleForSecond()}
      >
        {secondChild}
      </div>
    </div>
  );
}
