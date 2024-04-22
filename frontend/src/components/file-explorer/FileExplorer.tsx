import React from "react";
import {
  IoIosArrowBack,
  IoIosArrowForward,
  IoIosRefresh,
} from "react-icons/io";
import { twMerge } from "tailwind-merge";
import { WorkspaceFile, getWorkspace } from "#/services/fileService";
import ExplorerTree from "./ExplorerTree";
import { removeEmptyNodes } from "./utils";
import IconButton from "../IconButton";

interface ExplorerActionsProps {
  onRefresh: () => void;
  toggleHidden: () => void;
  isHidden: boolean;
}

function ExplorerActions({
  toggleHidden,
  onRefresh,
  isHidden,
}: ExplorerActionsProps) {
  return (
    <div
      className={twMerge(
        "transform flex h-[24px] items-center gap-1 absolute top-4 right-2",
        isHidden ? "right-3" : "right-2",
      )}
    >
      {!isHidden && (
        <IconButton
          icon={
            <IoIosRefresh
              size={20}
              className="text-neutral-400 hover:text-neutral-100 transition"
            />
          }
          testId="refresh"
          ariaLabel="Refresh workspace"
          onClick={onRefresh}
        />
      )}

      <IconButton
        icon={
          isHidden ? (
            <IoIosArrowForward
              size={20}
              className="text-neutral-400 hover:text-neutral-100 transition"
            />
          ) : (
            <IoIosArrowBack
              size={20}
              className="text-neutral-400 hover:text-neutral-100 transition"
            />
          )
        }
        testId="close"
        ariaLabel="Close workspace"
        onClick={toggleHidden}
      />
    </div>
  );
}

interface FileExplorerProps {
  onFileClick: (path: string) => void;
}

function FileExplorer({ onFileClick }: FileExplorerProps) {
  const [workspace, setWorkspace] = React.useState<WorkspaceFile>();
  const [isHidden, setIsHidden] = React.useState(false);

  const getWorkspaceData = async () => {
    const wsFile = await getWorkspace();
    setWorkspace(removeEmptyNodes(wsFile));
  };

  React.useEffect(() => {
    (async () => {
      await getWorkspaceData();
    })();
  }, []);

  return (
    <div
      className={twMerge(
        "bg-neutral-800 h-full border-r-1 border-r-neutral-600 flex flex-col transition-all ease-soft-spring overflow-auto",
        isHidden ? "min-w-[48px]" : "min-w-[228px]",
      )}
    >
      <div className="flex p-2 items-center justify-between relative">
        <div style={{ display: isHidden ? "none" : "block" }}>
          {workspace && (
            <ExplorerTree
              root={workspace}
              onFileClick={onFileClick}
              defaultOpen
            />
          )}
        </div>

        <ExplorerActions
          isHidden={isHidden}
          toggleHidden={() => setIsHidden((prev) => !prev)}
          onRefresh={getWorkspaceData}
        />
      </div>
    </div>
  );
}

export default FileExplorer;
