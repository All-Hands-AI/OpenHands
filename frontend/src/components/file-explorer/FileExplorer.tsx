import React from "react";
import {
  IoIosArrowBack,
  IoIosArrowForward,
  IoIosRefresh,
  IoIosCloudUpload,
} from "react-icons/io";
import { twMerge } from "tailwind-merge";
import { WorkspaceFile, getWorkspace, uploadFile } from "#/services/fileService";
import IconButton from "../IconButton";
import ExplorerTree from "./ExplorerTree";
import { removeEmptyNodes } from "./utils";

interface ExplorerActionsProps {
  onRefresh: () => void;
  onUpload: () => void;
  toggleHidden: () => void;
  isHidden: boolean;
}

function ExplorerActions({
  toggleHidden,
  onRefresh,
  onUpload,
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
        <>
          <IconButton
            icon={
              <IoIosRefresh
                size={16}
                className="text-neutral-400 hover:text-neutral-100 transition"
              />
            }
            testId="refresh"
            ariaLabel="Refresh workspace"
            onClick={onRefresh}
          />
          <IconButton
            icon={
              <IoIosCloudUpload
                size={16}
                className="text-neutral-400 hover:text-neutral-100 transition"
              />
            }
            testId="upload"
            ariaLabel="Upload File"
            onClick={onUpload}
          />
        </>
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
        testId="toggle"
        ariaLabel={isHidden ? "Open workspace" : "Close workspace"}
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
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  const getWorkspaceData = async () => {
    const wsFile = await getWorkspace();
    setWorkspace(removeEmptyNodes(wsFile));
  };

  const selectFileInput = () => {
    fileInputRef.current?.click(); // Trigger the file browser
  };

  const uploadFileData = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files ? event.target.files[0] : null;
    if (!file) {
      console.log("No file selected.");
      return;
    }
    console.log("File selected:", file);
    try {
      const response = await uploadFile(file);
      console.log(response);
      await getWorkspaceData(); // Refresh the workspace to show the new file
    } catch (error) {
      console.error("Error uploading file:", error);
    }
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
          onUpload={selectFileInput}
        />
      </div>
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={uploadFileData}
      />
    </div>
  );
}

export default FileExplorer;
