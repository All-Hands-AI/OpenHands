import React from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { useScrollToBottom } from "#/hooks/use-scroll-to-bottom";
import { JupyterCell } from "./jupyter-cell";
import { ScrollToBottomButton } from "#/components/shared/buttons/scroll-to-bottom-button";

interface JupyterEditorProps {
  maxWidth: number;
}

export function JupyterEditor({ maxWidth }: JupyterEditorProps) {
  const { cells } = useSelector((state: RootState) => state.jupyter);
  const jupyterRef = React.useRef<HTMLDivElement>(null);

  const { hitBottom, scrollDomToBottom, onChatBodyScroll } =
    useScrollToBottom(jupyterRef);

  return (
    <div className="flex-1" style={{ maxWidth }}>
      <div
        className="overflow-y-auto h-full"
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
