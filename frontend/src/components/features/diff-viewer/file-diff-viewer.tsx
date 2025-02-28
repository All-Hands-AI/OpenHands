import { DiffEditor } from "@monaco-editor/react";
import { useQuery } from "@tanstack/react-query";
import React from "react";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";
import { GitChangeStatus } from "#/api/open-hands.types";
import { getLanguageFromPath } from "#/utils/get-language-from-path";
import { cn } from "#/utils/utils";
import ChevronUp from "#/icons/chveron-up.svg?react";

export interface FileDiffViewerProps {
  path: string;
  type: GitChangeStatus;
}

export function FileDiffViewer({ path, type }: FileDiffViewerProps) {
  const { conversationId } = useConversation();
  const [isCollapsed, setIsCollapsed] = React.useState(true);

  const isAdded = type === "A" || type === "U";
  const isDeleted = type === "D";

  const {
    data: diff,
    isLoading,
    isSuccess,
    isRefetching,
  } = useQuery({
    queryKey: ["file_diff", conversationId, path, type],
    queryFn: () => {
      let filePath = path;
      if (type === "R") filePath = path.split("->")[1].trim();

      return OpenHands.getGitChangeDiff(conversationId, filePath);
    },
    enabled: !isCollapsed,
  });

  return (
    <div
      data-testid="file-diff-viewer-outer"
      className="w-full h-fit flex flex-col"
    >
      <div
        className={cn(
          "flex justify-between items-center px-2.5 py-3.5 border border-basic rounded-xl",
          !isCollapsed && !isLoading && "border-b-0 rounded-b-none",
        )}
      >
        <p className="text-sm text-content">
          <strong className="text-primary">{type === "U" ? "A" : type}</strong>{" "}
          {path}{" "}
          {isRefetching && (
            <span className="text-tertiary-light">
              | Getting latest changes...
            </span>
          )}
          {isLoading && (
            <span className="text-tertiary-light">| Loading...</span>
          )}
        </p>
        <button
          data-testid="collapse"
          type="button"
          onClick={() => setIsCollapsed((prev) => !prev)}
        >
          <ChevronUp
            className={cn(
              "w-4 h-4 transition-transform",
              isCollapsed && "transform rotate-180",
            )}
          />
        </button>
      </div>
      {isSuccess && (
        <div
          hidden={isCollapsed}
          className="w-full h-[700px] border border-basic"
        >
          <DiffEditor
            data-testid="file-diff-viewer"
            className="w-full h-full"
            language={getLanguageFromPath(path)}
            original={isAdded ? "" : diff.original}
            modified={isDeleted ? "" : diff.modified}
            theme="vs-dark"
            options={{
              renderValidationDecorations: "off",
              readOnly: true,
              renderSideBySide: !isAdded && !isDeleted,
              scrollBeyondLastLine: false,
              minimap: {
                enabled: false,
              },
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
