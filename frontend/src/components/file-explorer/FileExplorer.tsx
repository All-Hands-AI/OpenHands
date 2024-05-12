import React from "react";
import {
  IoIosArrowBack,
  IoIosArrowForward,
  IoIosRefresh,
  IoIosCloudUpload,
} from "react-icons/io";
import { twMerge } from "tailwind-merge";
import {
  Button,
  Dropdown,
  DropdownItem,
  DropdownMenu,
  DropdownTrigger,
} from "@nextui-org/react";
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
  onUpload: (type: "file" | "dir") => void;
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
          <Dropdown>
            <DropdownTrigger>
              <Button
                data-testid="upload"
                aria-label="Upload File"
                variant="flat"
                className="cursor-pointer text-[12px] bg-transparent aspect-square px-0 min-w-[20px] h-[20px]"
              >
                <IoIosCloudUpload
                  size={16}
                  className="text-neutral-400 hover:text-neutral-100 transition"
                />
              </Button>
            </DropdownTrigger>
            <DropdownMenu aria-label="Upload Actions">
              <DropdownItem key="file" onClick={() => onUpload("file")}>
                Upload File
              </DropdownItem>
              <DropdownItem key="directory" onClick={() => onUpload("dir")}>
                Upload Directory
              </DropdownItem>
            </DropdownMenu>
          </Dropdown>
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
  const directoryInputRef = React.useRef<HTMLInputElement | null>(null);

  const getWorkspaceData = async () => {
    const wsFile = await getWorkspace();
    setWorkspace(removeEmptyNodes(wsFile));
  };

  const selectFileInput = async (type: "file" | "dir") => {
    // Trigger the file browser
    if (type === "file") fileInputRef.current?.click();
    else directoryInputRef.current?.click();
  };

  const uploadFileData = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      try {
        await uploadFiles(event.target.files);
        await getWorkspaceData(); // Refresh the workspace to show the new file
      } catch (error) {
        toast.stickyError("ws", "Error uploading file");
      }
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
        data-testid="file-input"
        type="file"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={uploadFileData}
      />
      <input
        data-testid="dir-input"
        type="file"
        ref={directoryInputRef}
        // @ts-expect-error - required for browsers to recognize dir uploads
        // eslint-disable-next-line react/no-unknown-property
        directory=""
        webkitdirectory=""
        style={{ display: "none" }}
        onChange={uploadFileData}
      />
    </div>
  );
}

export default FileExplorer;
