import React from "react";
import { useRouteError } from "react-router";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useTranslation } from "react-i18next";
import { FileExplorer } from "#/components/features/file-explorer/file-explorer";
import { useFiles } from "#/context/files";
import { getLanguageFromPath } from "#/utils/get-language-from-path";

export function ErrorBoundary() {
  const error = useRouteError();
  const { t } = useTranslation();

  return (
    <div className="w-full h-full border border-danger rounded-b-xl flex flex-col items-center justify-center gap-2 bg-red-500/5">
      <h1 className="text-3xl font-bold">{t("ERROR$GENERIC")}</h1>
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
        {selectedPath && files[selectedPath] && (
          <div className="h-full w-full overflow-auto">
            <SyntaxHighlighter
              language={getLanguageFromPath(selectedPath)}
              style={vscDarkPlus}
              customStyle={{
                margin: 0,
                padding: "10px",
                height: "100%",
                background: "#171717",
                fontSize: "0.875rem",
                borderRadius: 0,
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
