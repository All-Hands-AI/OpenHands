import React from "react";
import TreeNode from "./TreeNode";

interface ExplorerTreeProps {
  tree: TreeNode[];
  onFileClick: (path: string) => void;
}

function ExplorerTree({ tree, onFileClick }: ExplorerTreeProps) {
  return (
    <div>
      {tree.map((branch, index) => (
        <TreeNode
          key={index}
          node={branch}
          path={branch.name}
          onFileClick={onFileClick}
        />
      ))}
    </div>
  );
}

export default ExplorerTree;
