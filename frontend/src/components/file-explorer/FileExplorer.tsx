import React from "react";
import {
  IoIosArrowBack,
  IoIosArrowForward,
  IoIosRefresh,
  IoIosCloudUpload,
} from "react-icons/io";
import { useDispatch, useSelector } from "react-redux";
import { IoFileTray } from "react-icons/io5";
import { useTranslation } from "react-i18next";
import { twMerge } from "tailwind-merge";
import AgentState from "#/types/AgentState";
import { setRefreshID } from "#/state/codeSlice";
import { listFiles, uploadFiles } from "#/services/fileService";
import IconButton from "../IconButton";
import ExplorerTree from "./ExplorerTree";
import toast from "#/utils/toast";
import { RootState } from "#/store";
import { I18nKey } from "#/i18n/declaration";

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
        "transform flex h-[24px] items-center gap-1",
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

function FileExplorer() {
  const [isHidden, setIsHidden] = React.useState(false);
  const [isDragging, setIsDragging] = React.useState(false);
  const [files, setFiles] = React.useState<string[] | null>(null);
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const selectFileInput = () => {
    fileInputRef.current?.click(); // Trigger the file browser
  };

  const refreshWorkspace = async () => {
    if (
      curAgentState === AgentState.LOADING ||
      curAgentState === AgentState.STOPPED
    ) {
      return;
    }
    dispatch(setRefreshID(Math.random()));
    try {
      const fileList = await listFiles();
      setFiles(fileList);
    } catch (error) {
      toast.error("refresh-error", t(I18nKey.EXPLORER$REFRESH_ERROR_MESSAGE));
    }
  };

  const uploadFileData = async (toAdd: FileList) => {
    try {
      const result = await uploadFiles(toAdd);

      if (result.error) {
        // Handle error response
        toast.error(
          `upload-error-${new Date().getTime()}`,
          result.error || t(I18nKey.EXPLORER$UPLOAD_ERROR_MESSAGE),
        );
        return;
      }

      const uploadedCount = result.uploadedFiles.length;
      const skippedCount = result.skippedFiles.length;

      if (uploadedCount > 0) {
        toast.success(
          `upload-success-${new Date().getTime()}`,
          t(I18nKey.EXPLORER$UPLOAD_SUCCESS_MESSAGE, {
            count: uploadedCount,
          }),
        );
      }

      if (skippedCount > 0) {
        const message = t(I18nKey.EXPLORER$UPLOAD_PARTIAL_SUCCESS_MESSAGE, {
          count: skippedCount,
        });
        toast.info(message);
      }

      if (uploadedCount === 0 && skippedCount === 0) {
        toast.info(t(I18nKey.EXPLORER$NO_FILES_UPLOADED_MESSAGE));
      }

      await refreshWorkspace();
    } catch (error) {
      // Handle unexpected errors (network issues, etc.)
      toast.error(
        `upload-error-${new Date().getTime()}`,
        t(I18nKey.EXPLORER$UPLOAD_ERROR_MESSAGE),
      );
    }
  };

  React.useEffect(() => {
    (async () => {
      await refreshWorkspace();
    })();
  }, [curAgentState]);

  React.useEffect(() => {
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
    <div className="relative h-full">
      {isDragging && (
        <div
          data-testid="dropzone"
          onDrop={(event) => {
            event.preventDefault();
            const { files: droppedFiles } = event.dataTransfer;
            if (droppedFiles.length > 0) {
              uploadFileData(droppedFiles);
            }
          }}
          onDragOver={(event) => event.preventDefault()}
          className="z-10 absolute flex flex-col justify-center items-center bg-black top-0 bottom-0 left-0 right-0 opacity-65"
        >
          <IoFileTray size={32} />
          <p className="font-bold text-xl">
            {t(I18nKey.EXPLORER$LABEL_DROP_FILES)}
          </p>
        </div>
      )}
      <div
        className={twMerge(
          "bg-neutral-800 h-full border-r-1 border-r-neutral-600 flex flex-col transition-all ease-soft-spring",
          isHidden ? "w-12" : "w-60",
        )}
      >
        <div className="flex flex-col relative h-full px-3 py-2">
          <div className="sticky top-0 bg-neutral-800 z-10">
            <div
              className={twMerge(
                "flex items-center",
                isHidden ? "justify-center" : "justify-between",
              )}
            >
              {!isHidden && (
                <div className="text-neutral-300 font-bold text-sm">
                  {t(I18nKey.EXPLORER$LABEL_WORKSPACE)}
                </div>
              )}
              <ExplorerActions
                isHidden={isHidden}
                toggleHidden={() => setIsHidden((prev) => !prev)}
                onRefresh={refreshWorkspace}
                onUpload={selectFileInput}
              />
            </div>
          </div>
          <div className="overflow-auto flex-grow">
            <div style={{ display: isHidden ? "none" : "block" }}>
              <ExplorerTree files={files} />
            </div>
          </div>
        </div>
        <input
          data-testid="file-input"
          type="file"
          multiple
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={(event) => {
            const { files: selectedFiles } = event.target;
            if (selectedFiles && selectedFiles.length > 0) {
              uploadFileData(selectedFiles);
            }
          }}
        />
      </div>
    </div>
  );
}

export default FileExplorer;
