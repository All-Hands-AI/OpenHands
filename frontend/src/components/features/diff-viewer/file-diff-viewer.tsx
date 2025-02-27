import { DiffEditor } from "@monaco-editor/react";
import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";

export interface FileDiffViewerProps {
  path: string;
}

export function FileDiffViewer({ path }: FileDiffViewerProps) {
  const { conversationId } = useConversation();

  const [isCollapsed, setIsCollapsed] = React.useState(true);

  const {
    data: diff,
    isLoading,
    isSuccess,
    isRefetching,
  } = useQuery({
    queryKey: ["file_diff", conversationId, path],
    queryFn: () => OpenHands.getGitChangeDiff(conversationId, path),
    enabled: !isCollapsed,
  });

  return (
    <div
      data-testid="file-diff-viewer-outer"
      className="w-full h-fit flex flex-col"
    >
      <div className="flex justify-between items-center px-2.5 py-3.5 border-b border-[#9099AC]">
        <p className="text-sm text-[#F9FBFE]">{path}</p>
        <button
          data-testid="collapse"
          type="button"
          onClick={() => setIsCollapsed((prev) => !prev)}
        >
          coll
        </button>
      </div>
      {isLoading && <div>Loading...</div>}
      {isRefetching && <div>Getting latest changes...</div>}
      {isSuccess && (
        <div hidden={isCollapsed} className="w-full h-[700px]">
          <DiffEditor
            data-testid="file-diff-viewer"
            className="w-full h-full"
            language="typescript"
            original={diff.original}
            modified={diff.modified}
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
      )}
    </div>
  );
}
