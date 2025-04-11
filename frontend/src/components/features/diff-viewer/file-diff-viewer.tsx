import { DiffEditor } from "@monaco-editor/react";
import React from "react";
import { editor as editor_t } from "monaco-editor";
import { useTranslation } from "react-i18next";
import { GitChangeStatus } from "#/api/open-hands.types";
import { getLanguageFromPath } from "#/utils/get-language-from-path";
import { cn } from "#/utils/utils";
import ChevronUp from "#/icons/chveron-up.svg?react";
import { useGitDiff } from "#/hooks/query/use-get-diff";
import { I18nKey } from "#/i18n/declaration";

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
  const { t } = useTranslation();
  const [isCollapsed, setIsCollapsed] = React.useState(true);
  const [editorHeight, setEditorHeight] = React.useState(400);
  const diffEditorRef = React.useRef<editor_t.IStandaloneDiffEditor>(null);

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

  // Function to update editor height based on content
  const updateEditorHeight = React.useCallback(() => {
    if (diffEditorRef.current) {
      const originalEditor = diffEditorRef.current.getOriginalEditor();
      const modifiedEditor = diffEditorRef.current.getModifiedEditor();

      if (originalEditor && modifiedEditor) {
        // Get the content height from both editors and use the larger one
        const originalHeight = originalEditor.getContentHeight();
        const modifiedHeight = modifiedEditor.getContentHeight();
        const contentHeight = Math.max(originalHeight, modifiedHeight);

        // Add a small buffer to avoid scrollbar
        setEditorHeight(contentHeight + 20);
      }
    }
  }, []);

  const handleEditorDidMount = (editor: editor_t.IStandaloneDiffEditor) => {
    diffEditorRef.current = editor;
    updateEditorHeight();

    const originalEditor = editor.getOriginalEditor();
    const modifiedEditor = editor.getModifiedEditor();

    originalEditor.onDidContentSizeChange(updateEditorHeight);
    modifiedEditor.onDidContentSizeChange(updateEditorHeight);
  };

  return (
    <div data-testid="file-diff-viewer-outer" className="w-full flex flex-col">
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
              | {t(I18nKey.DIFF_VIEWER$GETTING_LATEST_CHANGES)}
            </span>
          )}
          {isLoading && (
            <span className="text-tertiary-light">
              | {t(I18nKey.DIFF_VIEWER$LOADING)}
            </span>
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
      {isSuccess && !isCollapsed && (
        <div
          className="w-full border border-basic overflow-hidden"
          style={{ height: `${editorHeight}px` }}
        >
          <DiffEditor
            data-testid="file-diff-viewer"
            className="w-full h-full"
            language={getLanguageFromPath(filePath)}
            original={isAdded ? "" : diff.original}
            modified={isDeleted ? "" : diff.modified}
            theme="vs-dark"
            onMount={handleEditorDidMount}
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
              automaticLayout: true,
              scrollbar: {
                // Make scrollbar less intrusive
                alwaysConsumeMouseWheel: false,
              },
            }}
          />
        </div>
      )}
    </div>
  );
}
