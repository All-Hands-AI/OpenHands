import React from "react";
import { useRouteError } from "react-router";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { FileExplorer } from "#/components/features/file-explorer/file-explorer";
import { useFiles } from "#/context/files";
import { getLanguageFromPath } from "#/utils/get-language-from-path";

export function ErrorBoundary() {
  const error = useRouteError();

  return (
    <div className="w-full h-full border border-danger rounded-b-xl flex flex-col items-center justify-center gap-2 bg-red-500/5">
      <h1 className="text-3xl font-bold">Oops! An error occurred!</h1>
      {error instanceof Error && <pre>{error.message}</pre>}
    </div>
  );
}

function FileViewer() {
  const [fileExplorerIsOpen, setFileExplorerIsOpen] = React.useState(true);
  const { selectedPath, files } = useFiles();

  const toggleFileExplorer = () => {
    setFileExplorerIsOpen((prev) => !prev);
  };

  return (
    <div className="flex h-full bg-base-secondary relative">
      <FileExplorer isOpen={fileExplorerIsOpen} onToggle={toggleFileExplorer} />
      <div className="w-full h-full flex flex-col">
        {selectedPath && (
          <div className="flex w-full items-center justify-between self-end p-2">
            <span className="text-sm text-neutral-500">{selectedPath}</span>
          </div>
        )}
        {selectedPath && files[selectedPath] && (
          <div className="p-4 flex-1 overflow-auto">
            <SyntaxHighlighter
              language={getLanguageFromPath(selectedPath)}
              style={vscDarkPlus}
              customStyle={{
                margin: 0,
                background: "#171717",
                fontSize: "0.875rem",
              }}
            >
              {files[selectedPath]}
            </SyntaxHighlighter>
          </div>
        )}
      </div>
    </div>
  );
}

export default FileViewer;
