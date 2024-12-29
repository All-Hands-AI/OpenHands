import React from "react";
import { useRouteError } from "react-router";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
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

function getLanguageFromPath(path: string): string {
  const extension = path.split(".").pop()?.toLowerCase();
  switch (extension) {
    case "js":
    case "jsx":
      return "javascript";
    case "ts":
    case "tsx":
      return "typescript";
    case "py":
      return "python";
    case "html":
      return "html";
    case "css":
      return "css";
    case "json":
      return "json";
    case "md":
      return "markdown";
    case "yml":
    case "yaml":
      return "yaml";
    case "sh":
    case "bash":
      return "bash";
    case "dockerfile":
      return "dockerfile";
    case "rs":
      return "rust";
    case "go":
      return "go";
    case "java":
      return "java";
    case "cpp":
    case "cc":
    case "cxx":
      return "cpp";
    case "c":
      return "c";
    case "rb":
      return "ruby";
    case "php":
      return "php";
    case "sql":
      return "sql";
    default:
      return "text";
  }
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
