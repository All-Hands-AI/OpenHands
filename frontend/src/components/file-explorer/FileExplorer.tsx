import React from "react";
import {
  IoIosArrowBack,
  IoIosArrowForward,
  IoIosRefresh,
  IoIosCloudUpload,
} from "react-icons/io";
import { IoFileTray } from "react-icons/io5";
import { twMerge } from "tailwind-merge";
import {
  WorkspaceFile,
  getWorkspace,
  uploadFiles,
} from "#/services/fileService";
import IconButton from "../IconButton";
import ExplorerTree from "./ExplorerTree";
import { removeEmptyNodes } from "./utils";
import toast from "#/utils/toast";

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
  const [isDragging, setIsDragging] = React.useState(false);

  const fileInputRef = React.useRef<HTMLInputElement | null>(null);

  const getWorkspaceData = async () => {
    const wsFile = await getWorkspace();
    setWorkspace(removeEmptyNodes(wsFile));
  };

  const selectFileInput = async () => {
    // Trigger the file browser
    fileInputRef.current?.click();
  };

  const uploadFileData = async (files: FileList) => {
    try {
      await uploadFiles(files);
      await getWorkspaceData(); // Refresh the workspace to show the new file
    } catch (error) {
      toast.stickyError("ws", "Error uploading file");
    }
  };

  React.useEffect(() => {
    (async () => {
      await getWorkspaceData();
    })();

    const enableDragging = () => {
      setIsDragging(true);
    };

    const disableDragging = () => {
      setIsDragging(false);
    };

    document.addEventListener("dragenter", enableDragging);
    document.addEventListener("drop", disableDragging);

    return () => {
      document.removeEventListener("dragenter", enableDragging);
      document.removeEventListener("drop", disableDragging);
    };
  }, []);

  return (
    <div className="relative">
      {isDragging && (
        <div
          data-testid="dropzone"
          onDrop={(event) => {
            event.preventDefault();
            uploadFileData(event.dataTransfer.files);
          }}
          onDragOver={(event) => event.preventDefault()}
          className="z-10 absolute flex flex-col justify-center items-center bg-black top-0 bottom-0 left-0 right-0 opacity-65"
        >
          <IoFileTray size={32} />
          <p className="font-bold text-xl">Drop Files Here</p>
        </div>
      )}
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
          data-testid="file-input"
          type="file"
          multiple
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={(event) => {
            if (event.target.files) {
              uploadFileData(event.target.files);
            }
          }}
        />
      </div>
    </div>
  );
}

export default FileExplorer;
