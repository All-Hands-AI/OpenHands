import React from "react";
import TreeNode from "./TreeNode";

interface ExplorerTreeProps {
  tree: TreeNode[];
  onFileClick: (path: string) => void;
  defaultOpen?: boolean;
}

function ExplorerTree({
  tree,
  onFileClick,
  defaultOpen = true,
}: ExplorerTreeProps) {
  return (
    <div>
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
  defaultOpen: true,
};

export default ExplorerTree;
