import React from "react";
import TreeNode from "./TreeNode";

interface ExplorerTreeProps {
  files: string[];
  defaultOpen?: boolean;
}

function ExplorerTree({ files, defaultOpen = false }: ExplorerTreeProps) {
  return (
    <div className="w-full overflow-x-auto h-full pt-[4px] bg-editor-sidebar text-editor-base dark:text-editor-base">
      {files.map((file) => (
        <TreeNode key={file} path={file} defaultOpen={defaultOpen} />
      ))}
    </div>
  );
}

export default ExplorerTree;
