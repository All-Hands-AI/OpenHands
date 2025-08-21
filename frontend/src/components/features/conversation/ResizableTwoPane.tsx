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

type PanelDimension = {
  width: number;
  height: number;
};

export function ResizableTwoPane({ children }: ResizableTwoPaneProps) {
  const [first, second] = children;

  const [panelDimension, setPanelDimension] = useState<PanelDimension>({
    width: 0,
    height: 0,
  });
  const { width } = useWindowSize();

  const [minConstraint, maxConstraint] = useMemo(() => {
    const OFFSET = 320;
    return [OFFSET, Math.max((width ?? 0) - OFFSET, 0)];
  }, [width]);

  const containerRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    setPanelDimension({ width: el.clientWidth / 2, height: el.clientHeight });

    const ro = new ResizeObserver(() => {
      setPanelDimension({ width: el.clientWidth, height: el.clientHeight });
    });
    ro.observe(el);
    // eslint-disable-next-line consistent-return
    return ro.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      className={cn(
        "grow flex",
        "w-full h-full overflow-y-scroll",
        "flex-row justify-center h-full",
      )}
    >
      <ResizableBox
        width={panelDimension.width}
        height={panelDimension.height ?? 1}
        axis="x"
        minConstraints={[minConstraint, panelDimension.height ?? 1]}
        maxConstraints={[maxConstraint, panelDimension.height ?? 1]}
        onResize={(_, data) =>
          setPanelDimension({
            width: data.size.width,
            height: data.size.height,
          })
        }
        onResizeStop={(_, data) =>
          setPanelDimension({
            width: data.size.width,
            height: data.size.height,
          })
        }
        className="flex"
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
