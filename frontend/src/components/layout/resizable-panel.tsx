import React, {
  CSSProperties,
  JSX,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  VscChevronDown,
  VscChevronLeft,
  VscChevronRight,
  VscChevronUp,
} from "react-icons/vsc";
import { twMerge } from "tailwind-merge";
import { IconButton } from "../shared/buttons/icon-button";

export enum Orientation {
  HORIZONTAL = "horizontal",
  VERTICAL = "vertical",
}

enum Collapse {
  COLLAPSED = "collapsed",
  SPLIT = "split",
  FILLED = "filled",
}

type ResizablePanelProps = {
  firstChild: React.ReactNode;
  firstClassName: string | undefined;
  secondChild: React.ReactNode;
  secondClassName: string | undefined;
  className: string | undefined;
  orientation: Orientation;
  initialSize: number;
};

export function ResizablePanel({
  firstChild,
  firstClassName,
  secondChild,
  secondClassName,
  className,
  orientation,
  initialSize,
}: ResizablePanelProps): JSX.Element {
  const isHorizontal = orientation === Orientation.HORIZONTAL;
  const getConstraints = useCallback(
    () => ({
      min: isHorizontal ? 350 : 300,
      max: isHorizontal ? window.innerWidth * 0.5 : window.innerHeight * 0.7,
    }),
    [isHorizontal],
  );

  const constrainSize = useCallback(
    (size: number) => {
      const { min, max } = getConstraints();
      return Math.min(Math.max(size, min), max);
    },
    [getConstraints],
  );

  const [firstSize, setFirstSize] = useState(() => constrainSize(initialSize));
  const [dividerPosition, setDividerPosition] = useState<number | null>(null);
  const [collapse, setCollapse] = useState(Collapse.SPLIT);
  const firstRef = useRef<HTMLDivElement>(null);
  const secondRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleResize = () => setFirstSize(constrainSize(firstSize));
    const timeoutId = setTimeout(handleResize, 100);
    window.addEventListener("resize", handleResize);
    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener("resize", handleResize);
    };
  }, [firstSize, constrainSize]);

  useEffect(() => {
    if (!dividerPosition) return undefined;

    const onMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      const delta = (isHorizontal ? e.clientX : e.clientY) - dividerPosition;
      setFirstSize(constrainSize(firstSize + delta));
      setDividerPosition(isHorizontal ? e.clientX : e.clientY);
    };

    const onMouseUp = (e: MouseEvent) => {
      e.preventDefault();
      if (firstRef.current) firstRef.current.style.transition = "";
      if (secondRef.current) secondRef.current.style.transition = "";
      setFirstSize(
        constrainSize(
          firstSize +
            ((isHorizontal ? e.clientX : e.clientY) - dividerPosition),
        ),
      );
      setDividerPosition(null);
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };
  }, [dividerPosition, firstSize, isHorizontal, constrainSize]);

  const onMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    if (firstRef.current) firstRef.current.style.transition = "none";
    if (secondRef.current) secondRef.current.style.transition = "none";
    setDividerPosition(isHorizontal ? e.clientX : e.clientY);
  };

  const getPanelStyle = useCallback(
    (isFirst: boolean): CSSProperties => {
      const style: CSSProperties = { overflow: "hidden" };
      const { min } = getConstraints();
      const isHidden =
        (isFirst && collapse === Collapse.COLLAPSED) ||
        (!isFirst && collapse === Collapse.FILLED);

      const hiddenStyle: CSSProperties = {
        ...style,
        opacity: 0,
        width: 0,
        minWidth: 0,
        height: 0,
        minHeight: 0,
      };

      const expandedStyle: CSSProperties = { ...style, flexGrow: 1 };

      if (isHidden) {
        return hiddenStyle;
      }

      if (collapse !== Collapse.SPLIT) {
        return expandedStyle;
      }

      if (isFirst) {
        const dimension = isHorizontal ? "width" : "height";
        const minDimension = isHorizontal ? "minWidth" : "minHeight";
        const maxDimension = isHorizontal ? "maxWidth" : "maxHeight";

        const firstPanelStyle: CSSProperties = {
          ...style,
          [dimension]: `${firstSize}px`,
          [minDimension]: `${min}px`,
          [maxDimension]: isHorizontal ? "50%" : "70%",
          flexShrink: 0,
        };
        return firstPanelStyle;
      }

      const secondPanelStyle: CSSProperties = {
        ...style,
        flexGrow: 1,
        flexShrink: 1,
        ...(isHorizontal
          ? {
              minWidth: "30%",
              maxWidth: "70%",
            }
          : {
              minHeight: "300px",
              display: "flex",
              flexDirection: "column",
            }),
      };
      return secondPanelStyle;
    },
    [collapse, firstSize, isHorizontal, getConstraints],
  );

  const toggleCollapse = () =>
    setCollapse(
      collapse === Collapse.SPLIT ? Collapse.COLLAPSED : Collapse.SPLIT,
    );

  const toggleExpand = () =>
    setCollapse(collapse === Collapse.SPLIT ? Collapse.FILLED : Collapse.SPLIT);

  return (
    <div className={twMerge("flex", !isHorizontal && "flex-col", className)}>
      <div
        ref={firstRef}
        className={twMerge(firstClassName, "transition-all ease-soft-spring")}
        style={getPanelStyle(true)}
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
          onClick={toggleCollapse}
        />
        <IconButton
          icon={isHorizontal ? <VscChevronRight /> : <VscChevronDown />}
          ariaLabel="Expand"
          onClick={toggleExpand}
        />
      </div>
      <div
        ref={secondRef}
        className={twMerge(secondClassName, "transition-all ease-soft-spring")}
        style={getPanelStyle(false)}
      >
        {secondChild}
      </div>
    </div>
  );
}
