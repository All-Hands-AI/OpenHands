import React from "react";
import TreeNode from "./TreeNode";
import { WorkspaceFile, listFiles } from "#/services/fileService";

interface ExplorerTreeProps {
  root: WorkspaceFile;
  onFileClick: (path: string) => void;
  defaultOpen?: boolean;
}

function ExplorerTree({
  onFileClick,
  defaultOpen = false,
}: ExplorerTreeProps) {
  const [files, setFiles] = React.useState<string[]>([]);

  React.useEffect(() => {
    listFiles().then((files) => {
      setFiles(files);
    });
  }, []);

  return (
    <div className="w-full overflow-x-auto h-full pt-[4px]">
      {files.map((file) => (
        <TreeNode
          key={file}
          path={file}
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
