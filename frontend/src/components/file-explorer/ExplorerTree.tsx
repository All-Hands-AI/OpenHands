import React from "react";
import TreeNode from "./TreeNode";
import { WorkspaceFile } from "../../services/fileService";

interface ExplorerTreeProps {
  tree: WorkspaceFile[];
  onFileClick: (path: string) => void;
  defaultOpen?: boolean;
}

function ExplorerTree({
  tree,
  onFileClick,
  defaultOpen = false,
}: ExplorerTreeProps) {
  return (
    <div className="w-full overflow-x-auto h-full pt-[4px]">
      {tree.map((branch, index) => (
        <TreeNode
          key={index}
          node={branch}
          path={branch.name}
          onFileClick={onFileClick}
          defaultOpen={defaultOpen}
        />
      ))}
    </div>
  );
}

ExplorerTree.defaultProps = {
  defaultOpen: false,
};

export default ExplorerTree;
