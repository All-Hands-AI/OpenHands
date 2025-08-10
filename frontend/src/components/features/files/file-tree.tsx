/* eslint-disable i18next/no-literal-string */
import React from "react";
import OpenHands from "#/api/open-hands";

interface FileTreeProps {
  conversationId: string;
  rootPath?: string | null;
  onOpenFile: (path: string) => void;
}

export function FileTree({
  conversationId,
  rootPath = null,
  onOpenFile,
}: FileTreeProps) {
  const [paths, setPaths] = React.useState<string[]>([]);
  const [currentPath, setCurrentPath] = React.useState<string | null>(rootPath);
  const [isLoading, setIsLoading] = React.useState(false);

  const loadTree = React.useCallback(
    async (path?: string | null) => {
      setIsLoading(true);
      try {
        const list = await OpenHands.getRepoTree(
          conversationId,
          path || undefined,
        );
        setPaths(list);
        setCurrentPath(path || null);
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId],
  );

  React.useEffect(() => {
    loadTree(rootPath);
  }, [rootPath, loadTree]);

  const handleOpen = (p: string) => {
    if (p.endsWith("/")) {
      loadTree(p);
    } else {
      onOpenFile(p);
    }
  };

  return (
    <div className="flex flex-col gap-1 text-sm">
      <div className="flex items-center justify-between">
        <div className="font-medium">{currentPath || "."}</div>
        {isLoading && <div className="text-xs opacity-60">Loading...</div>}
      </div>
      <ul className="max-h-[60vh] overflow-auto">
        {paths.map((p) => (
          <li key={p}>
            <button
              className="text-left w-full hover:bg-tertiary rounded px-2 py-1"
              type="button"
              onClick={() => handleOpen(p)}
            >
              {p}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
