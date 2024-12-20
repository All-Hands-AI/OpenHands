import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { ExplorerTree } from "#/components/features/file-explorer/explorer-tree";
import toast from "#/utils/toast";
import { RootState } from "#/store";
import { I18nKey } from "#/i18n/declaration";
import { useListFiles } from "#/hooks/query/use-list-files";
import { FileUploadSuccessResponse } from "#/api/open-hands.types";
import { useUploadFiles } from "#/hooks/mutation/use-upload-files";
import { cn } from "#/utils/utils";
import { Dropzone } from "./dropzone";
import { FileExplorerHeader } from "./file-explorer-header";
import { useVSCodeUrl } from "#/hooks/query/use-vscode-url";
import { OpenVSCodeButton } from "#/components/shared/buttons/open-vscode-button";
import { addAssistantMessage } from "#/state/chat-slice";
import {
  useWsClient,
  WsClientProviderStatus,
} from "#/context/ws-client-provider";

interface FileExplorerProps {
  isOpen: boolean;
  onToggle: () => void;
}

export function FileExplorer({ isOpen, onToggle }: FileExplorerProps) {
  const { status } = useWsClient();
  const { t } = useTranslation();
  const dispatch = useDispatch();

  const fileInputRef = React.useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = React.useState(false);

  const { curAgentState } = useSelector((state: RootState) => state.agent);

  const { data: paths, refetch, error } = useListFiles();
  const { mutate: uploadFiles } = useUploadFiles();
  const { data: vscodeUrl } = useVSCodeUrl({
    enabled: !RUNTIME_INACTIVE_STATES.includes(curAgentState),
  });

  const handleOpenVSCode = () => {
    if (vscodeUrl?.vscode_url) {
      dispatch(
        addAssistantMessage(
          "You opened VS Code. Please inform the agent of any changes you made to the workspace or environment. To avoid conflicts, it's best to pause the agent before making any changes.",
        ),
      );
      window.open(vscodeUrl.vscode_url, "_blank");
    } else if (vscodeUrl?.error) {
      toast.error(
        `open-vscode-error-${new Date().getTime()}`,
        t(I18nKey.EXPLORER$VSCODE_SWITCHING_ERROR_MESSAGE, {
          error: vscodeUrl.error,
        }),
      );
    }
  };

  const selectFileInput = () => {
    fileInputRef.current?.click(); // Trigger the file browser
  };

  const handleUploadSuccess = (data: FileUploadSuccessResponse) => {
    const uploadedCount = data.uploaded_files.length;
    const skippedCount = data.skipped_files.length;

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
  };

  const handleUploadError = (uploadError: Error) => {
    toast.error(
      `upload-error-${new Date().getTime()}`,
      uploadError.message || t(I18nKey.EXPLORER$UPLOAD_ERROR_MESSAGE),
    );
  };

  const refreshWorkspace = () => {
    if (!RUNTIME_INACTIVE_STATES.includes(curAgentState)) {
      refetch();
    }
  };

  const uploadFileData = (files: FileList) => {
    uploadFiles(
      { files: Array.from(files) },
      { onSuccess: handleUploadSuccess, onError: handleUploadError },
    );
    refreshWorkspace();
  };

  const handleDropFiles = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const { files: droppedFiles } = event.dataTransfer;
    if (droppedFiles.length > 0) {
      uploadFileData(droppedFiles);
    }
    setIsDragging(false);
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
        <Dropzone
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDropFiles}
        />
      )}
      <div
        className={cn(
          "bg-neutral-800 h-full border-r-1 border-r-neutral-600 flex flex-col",
          !isOpen ? "w-12" : "w-60",
        )}
      >
        <div className="flex flex-col relative h-full px-3 py-2 overflow-hidden">
          <FileExplorerHeader
            isOpen={isOpen}
            onToggle={onToggle}
            onRefreshWorkspace={refreshWorkspace}
            onUploadFile={selectFileInput}
          />
          {!error && (
            <div className="overflow-auto flex-grow min-h-0">
              <div style={{ display: !isOpen ? "none" : "block" }}>
                <ExplorerTree files={paths || []} />
              </div>
            </div>
          )}
          {error && (
            <div className="flex flex-col items-center justify-center h-full">
              <p className="text-neutral-300 text-sm">{error.message}</p>
            </div>
          )}
          {isOpen && (
            <OpenVSCodeButton
              onClick={handleOpenVSCode}
              isDisabled={status === WsClientProviderStatus.DISCONNECTED}
            />
          )}
        </div>
      </div>
    </div>
  );
}
