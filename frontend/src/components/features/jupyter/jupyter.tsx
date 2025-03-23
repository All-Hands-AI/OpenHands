import React from "react";
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom";
import { JupyterCell } from "./jupyter-cell";
import { ScrollToBottomButton } from "#/components/shared/buttons/scroll-to-bottom-button";
import { useJupyter } from "#/hooks/query/use-jupyter";

interface JupyterEditorProps {
  maxWidth: number;
}

export function JupyterEditor({ maxWidth }: JupyterEditorProps) {
  const { cells } = useJupyter();
  const jupyterRef = React.useRef<HTMLDivElement>(null);

  // Debug log
  // eslint-disable-next-line no-console
  console.log("[Jupyter Debug] Rendering jupyter with cells:", {
    cellsLength: cells.length,
  });

  const { hitBottom, scrollDomToBottom, onChatBodyScroll } =
    useScrollToBottom(jupyterRef);

  return (
    <div className="flex-1 h-full flex flex-col" style={{ maxWidth }}>
      <div
        data-testid="jupyter-container"
        className="flex-1 overflow-y-auto"
        ref={jupyterRef}
        onScroll={(e) => onChatBodyScroll(e.currentTarget)}
      >
        {cells.map((cell, index) => (
          <JupyterCell key={index} cell={cell} />
        ))}
      </div>
      {!hitBottom && (
        <div className="sticky bottom-2 flex items-center justify-center">
          <ScrollToBottomButton onClick={scrollDomToBottom} />
        </div>
      )}
    </div>
  );
}
