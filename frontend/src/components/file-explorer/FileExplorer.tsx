import React from "react";
import {
  IoIosArrowBack,
  IoIosArrowForward,
  IoIosRefresh,
  IoIosCloudUpload,
} from "react-icons/io";
import { useRevalidator } from "@remix-run/react";
import { useDispatch, useSelector } from "react-redux";
import { IoFileTray } from "react-icons/io5";
import { useTranslation } from "react-i18next";
import { twMerge } from "tailwind-merge";
import AgentState from "#/types/AgentState";
import { setRefreshID } from "#/state/codeSlice";
import { addAssistantMessage } from "#/state/chatSlice";
import IconButton from "../IconButton";
import ExplorerTree from "./ExplorerTree";
import toast from "#/utils/toast";
import { RootState } from "#/store";
import { I18nKey } from "#/i18n/declaration";
import OpenHands from "#/api/open-hands";
import { useFiles } from "#/context/files";
import { isOpenHandsErrorResponse } from "#/api/open-hands.utils";
import VSCodeIcon from "#/assets/vscode-alt.svg?react";

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

interface FileExplorerProps {
  isOpen: boolean;
  onToggle: () => void;
  error: string | null;
}

function FileExplorer({ error, isOpen, onToggle }: FileExplorerProps) {
  const { revalidate } = useRevalidator();

  const { paths, setPaths } = useFiles();
  const [isDragging, setIsDragging] = React.useState(false);

  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const dispatch = useDispatch();
  const { t } = useTranslation();
  const selectFileInput = () => {
    fileInputRef.current?.click(); // Trigger the file browser
  };

  const refreshWorkspace = () => {
    if (
      curAgentState === AgentState.LOADING ||
      curAgentState === AgentState.STOPPED
    ) {
      return;
    }
    dispatch(setRefreshID(Math.random()));
    OpenHands.getFiles().then(setPaths);
    revalidate();
  };

  const uploadFileData = async (files: FileList) => {
    try {
      const result = await OpenHands.uploadFiles(Array.from(files));

      if (isOpenHandsErrorResponse(result)) {
        // Handle error response
        toast.error(
          `upload-error-${new Date().getTime()}`,
          result.error || t(I18nKey.EXPLORER$UPLOAD_ERROR_MESSAGE),
        );
        return;
      }

      const uploadedCount = result.uploaded_files.length;
      const skippedCount = result.skipped_files.length;

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

      refreshWorkspace();
    } catch (e) {
      // Handle unexpected errors (network issues, etc.)
      toast.error(
        `upload-error-${new Date().getTime()}`,
        t(I18nKey.EXPLORER$UPLOAD_ERROR_MESSAGE),
      );
    }
  };

  const handleVSCodeClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    try {
      const response = await OpenHands.getVSCodeUrl();
      if (response.vscode_url) {
        dispatch(
          addAssistantMessage(
            "You opened VS Code. Please inform the agent of any changes you made to the workspace or environment. To avoid conflicts, it's best to pause the agent before making any changes.",
          ),
        );
        window.open(response.vscode_url, "_blank");
      } else {
        toast.error(
          `open-vscode-error-${new Date().getTime()}`,
          t(I18nKey.EXPLORER$VSCODE_SWITCHING_ERROR_MESSAGE, {
            error: response.error,
          }),
        );
      }
    } catch (exp_error) {
      toast.error(
        `open-vscode-error-${new Date().getTime()}`,
        t(I18nKey.EXPLORER$VSCODE_SWITCHING_ERROR_MESSAGE, {
          error: String(exp_error),
        }),
      );
    }
  };

  React.useEffect(() => {
    refreshWorkspace();
  }, [curAgentState]);

  return (
    <div
      data-testid="file-explorer"
      className="relative h-full"
      onDragEnter={() => {
        setIsDragging(true);
      }}
      onDragEnd={() => {
        setIsDragging(false);
      }}
    >
      {isDragging && (
        <div
          data-testid="dropzone"
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            const { files: droppedFiles } = event.dataTransfer;
            if (droppedFiles.length > 0) {
              uploadFileData(droppedFiles);
            }
            setIsDragging(false);
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
          "bg-neutral-800 h-full border-r-1 border-r-neutral-600 flex flex-col",
          !isOpen ? "w-12" : "w-60",
        )}
      >
        <div className="flex flex-col relative h-full px-3 py-2 overflow-hidden">
          <div className="sticky top-0 bg-neutral-800">
            <div
              className={twMerge(
                "flex items-center",
                !isOpen ? "justify-center" : "justify-between",
              )}
            >
              {isOpen && (
                <div className="text-neutral-300 font-bold text-sm">
                  {t(I18nKey.EXPLORER$LABEL_WORKSPACE)}
                </div>
              )}
              <ExplorerActions
                isHidden={!isOpen}
                toggleHidden={onToggle}
                onRefresh={refreshWorkspace}
                onUpload={selectFileInput}
              />
            </div>
          </div>
          {!error && (
            <div className="overflow-auto flex-grow min-h-0">
              <div style={{ display: !isOpen ? "none" : "block" }}>
                <ExplorerTree files={paths} />
              </div>
            </div>
          )}
          {error && (
            <div className="flex flex-col items-center justify-center h-full">
              <p className="text-neutral-300 text-sm">{error}</p>
            </div>
          )}
          {isOpen && (
            <button
              type="button"
              onClick={handleVSCodeClick}
              disabled={
                curAgentState === AgentState.INIT ||
                curAgentState === AgentState.LOADING
              }
              className={twMerge(
                "mt-auto mb-2 w-full h-10 text-white rounded flex items-center justify-center gap-2 transition-colors",
                curAgentState === AgentState.INIT ||
                  curAgentState === AgentState.LOADING
                  ? "bg-neutral-600 cursor-not-allowed"
                  : "bg-[#4465DB] hover:bg-[#3451C7]",
              )}
              aria-label="Open in VS Code"
            >
              <VSCodeIcon width={20} height={20} />
              Open in VS Code
            </button>
          )}
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