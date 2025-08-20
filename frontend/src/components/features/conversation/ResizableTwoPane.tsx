import { useWindowSize } from "@uidotdev/usehooks";
import React, {
  ReactElement,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { ResizableBox } from "react-resizable";
import { cn } from "#/utils/utils";
import "react-resizable/css/styles.css";

type ResizableTwoPaneProps = {
  children: [ReactElement, ReactElement];
};

export function ResizableTwoPane({ children }: ResizableTwoPaneProps) {
  const [first, second] = children;
  const [[paneWidth, paneHeight], setPaneDim] = useState<[number, number]>([
    0, 0,
  ]);
  const { width } = useWindowSize();

  const [minConstraint, maxConstraint] = useMemo(() => {
    const OFFSET = 320;
    return [OFFSET, Math.max((width ?? 0) - 320, 0)];
  }, [width]);

  const containerRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const update = () => {
      setPaneDim([el.clientWidth, el.clientHeight]);
    };

    setPaneDim([el.clientWidth / 2, el.clientHeight]);

    const ro = new ResizeObserver(update);
    ro.observe(el);
    // eslint-disable-next-line consistent-return
    return ro.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      className={cn(
        "grow flex",
        "w-full h-full overflow-y-scroll relative",
        "flex-row justify-center h-full",
      )}
    >
      <ResizableBox
        width={paneWidth}
        height={paneHeight ?? 1}
        axis="x"
        minConstraints={[minConstraint, paneHeight ?? 1]}
        maxConstraints={[maxConstraint, paneHeight ?? 1]}
        onResize={(_, data) => setPaneDim([data.size.width, data.size.height])}
        onResizeStop={(_, data) =>
          setPaneDim([data.size.width, data.size.height])
        }
        className={cn("flex")}
        handle={
          <div
            className="absolute top-0 right-0 w-2.5 h-full cursor-col-resize flex items-center justify-center z-2"
            role="separator"
            aria-orientation="vertical"
          />
        }
        handleSize={[10, 10]}
      >
        <div className="flex flex-1">{first}</div>
      </ResizableBox>
      {second}
    </div>
  );
}
