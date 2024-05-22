import React from "react";
import TreeNode from "./TreeNode";

interface ExplorerTreeProps {
  files: string[];
  defaultOpen?: boolean;
}

function ExplorerTree({ files, defaultOpen = false }: ExplorerTreeProps) {
  return (
    <div className="w-full overflow-x-auto h-full pt-[4px]">
      {files.map((file) => (
        <TreeNode key={file} path={file} defaultOpen={defaultOpen} />
      ))}
    </div>
  );
}

ExplorerTree.defaultProps = {
  defaultOpen: false,
};

export default ExplorerTree;
