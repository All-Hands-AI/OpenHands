import { DiffEditor } from "@monaco-editor/react";
import React from "react";
import { GitChangeStatus } from "#/api/open-hands.types";
import { getLanguageFromPath } from "#/utils/get-language-from-path";
import { cn } from "#/utils/utils";
import ChevronUp from "#/icons/chveron-up.svg?react";
import { useGitDiff } from "#/hooks/query/use-get-diff";

const STATUS_MAP: Record<GitChangeStatus, string> = {
  A: "Added",
  D: "Deleted",
  M: "Modified",
  R: "Renamed",
  U: "Untracked",
};

export interface FileDiffViewerProps {
  path: string;
  type: GitChangeStatus;
}

export function FileDiffViewer({ path, type }: FileDiffViewerProps) {
  const [isCollapsed, setIsCollapsed] = React.useState(true);

  const isAdded = type === "A" || type === "U";
  const isDeleted = type === "D";

  const filePath = React.useMemo(() => {
    if (type === "R") {
      const parts = path.split(/\s+/).slice(1);
      return parts[parts.length - 1];
    }

    return path;
  }, [path, type]);

  const {
    data: diff,
    isLoading,
    isSuccess,
    isRefetching,
  } = useGitDiff({
    filePath,
    type,
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
          <strong className="text-primary uppercase">
            {type === "U" ? STATUS_MAP.A : STATUS_MAP[type]}
          </strong>{" "}
          {filePath}{" "}
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
