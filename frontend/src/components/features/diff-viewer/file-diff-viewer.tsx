import { DiffEditor } from "@monaco-editor/react";
import React from "react";

export interface FileDiffViewerProps {
  label: string;
  original: string;
  modified: string;
}

export function FileDiffViewer({
  label,
  original,
  modified,
}: FileDiffViewerProps) {
  const [isCollapsed, setIsCollapsed] = React.useState(false);

  return (
    <div
      data-testid="file-diff-viewer-outer"
      className="w-full h-fit flex flex-col"
    >
      <div className="flex justify-between items-center px-2.5 py-3.5 border-b border-[#9099AC]">
        <p className="text-sm text-[#F9FBFE]">{label}</p>
        <button
          data-testid="collapse"
          type="button"
          onClick={() => setIsCollapsed((prev) => !prev)}
        >
          coll
        </button>
      </div>
      <div hidden={isCollapsed} className="w-full h-[700px]">
        <DiffEditor
          data-testid="file-diff-viewer"
          className="w-full h-full"
          language="typescript"
          original={original}
          modified={modified}
          theme="vs-dark"
          options={{
            renderValidationDecorations: "off",
            readOnly: true,
            renderSideBySide: true,
            hideUnchangedRegions: {
              enabled: true,
            },
          }}
        />
      </div>
    </div>
  );
}
