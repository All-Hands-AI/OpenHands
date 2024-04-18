import React from "react";
import { getWorkspace } from "../../services/fileService";
import ExplorerTree from "./ExplorerTree";
import { removeEmptyNodes } from "./utils";

interface FileExplorerProps {
  onFileClick: (path: string) => void;
}

function FileExplorer({ onFileClick }: FileExplorerProps) {
  const [workspace, setWorkspace] = React.useState<TreeNode[]>([]);
  const [isHidden, setIsHidden] = React.useState(false);

  const getWorkspaceData = async () => {
    const wsFile = await getWorkspace();
    setWorkspace(removeEmptyNodes([wsFile]));
  };

  React.useEffect(() => {
    (async () => {
      await getWorkspaceData();
    })();
  }, []);

  return (
    <div>
      <div style={{ display: isHidden ? "none" : "block" }}>
        <ExplorerTree tree={workspace} onFileClick={onFileClick} />
      </div>

      <button
        data-testid="close"
        type="button"
        onClick={() => setIsHidden((prev) => !prev)}
      >
        {isHidden ? "Open" : "Close"}
      </button>
      <button
        data-testid="refresh"
        type="button"
        onClick={async () => getWorkspaceData()}
      >
        Refresh
      </button>
    </div>
  );
}

export default FileExplorer;
