import React from "react";
import { useRouteError } from "react-router";
import { FileExplorer } from "#/components/features/file-explorer/file-explorer";
import { useFiles } from "#/context/files";

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
    <div className="flex h-full bg-neutral-900 relative">
      <FileExplorer isOpen={fileExplorerIsOpen} onToggle={toggleFileExplorer} />
      <div className="w-full">
        {selectedPath && (
          <div className="flex w-full items-center justify-between self-end p-2">
            <span className="text-sm text-neutral-500">{selectedPath}</span>
          </div>
        )}
        {selectedPath && (
          <pre className="p-4 text-sm text-neutral-300 font-mono whitespace-pre-wrap">
            {files[selectedPath]}
          </pre>
        )}
      </div>
    </div>
  );
}

export default FileViewer;
