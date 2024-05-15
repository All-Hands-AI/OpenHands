import React from "react";
import TreeNode from "./TreeNode";
import { WorkspaceFile } from "#/services/fileService";

interface ExplorerTreeProps {
  root: WorkspaceFile;
  onFileClick: (path: string) => void;
  defaultOpen?: boolean;
}

function ExplorerTree({
  onFileClick,
  defaultOpen = false,
}: ExplorerTreeProps) {
  return (
    <div className="w-full overflow-x-auto h-full pt-[4px]">
      <TreeNode
        path="/"
        onFileClick={onFileClick}
        defaultOpen={defaultOpen}
      />
    </div>
  );
}

ExplorerTree.defaultProps = {
  defaultOpen: false,
};

export default ExplorerTree;
