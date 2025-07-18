import React from "react";
import { JupyterEditor } from "#/components/features/jupyter/jupyter";

function Jupyter() {
  const parentRef = React.useRef<HTMLDivElement>(null);
  const [parentWidth, setParentWidth] = React.useState(0);

  // This is a hack to prevent the editor from overflowing
  // Should be removed after revising the parent and containers
  // Use ResizeObserver to properly track parent width changes
  React.useEffect(() => {
    let resizeObserver: ResizeObserver | null = null;

    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        // Use contentRect.width for more accurate measurements
        const { width } = entry.contentRect;
        if (width > 0) {
          setParentWidth(width);
        }
      }
    });

    if (parentRef.current) {
      resizeObserver.observe(parentRef.current);
    }

    return () => {
      resizeObserver?.disconnect();
    };
  }, []);

  // Provide a fallback width to prevent the editor from being hidden
  // Use parentWidth if available, otherwise use a large default
  const maxWidth = parentWidth > 0 ? parentWidth : 9999;

  return (
    <div ref={parentRef} className="h-full">
      <JupyterEditor maxWidth={maxWidth} />
    </div>
  );
}

export default Jupyter;
