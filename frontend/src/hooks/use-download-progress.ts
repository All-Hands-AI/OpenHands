import { useCallback, useEffect, useRef, useState } from "react";
import { downloadFiles } from "#/utils/download-files";
import { DownloadProgressState } from "#/components/shared/download-progress";
import { useConversation } from "#/context/conversation-context";

export const INITIAL_PROGRESS: DownloadProgressState = {
  filesTotal: 0,
  filesDownloaded: 0,
  currentFile: "",
  totalBytesDownloaded: 0,
  bytesDownloadedPerSecond: 0,
  isDiscoveringFiles: true,
};

export function useDownloadProgress(
  initialPath: string | undefined,
  onClose: () => void,
) {
  const [isStarted, setIsStarted] = useState(false);
  const [progress, setProgress] =
    useState<DownloadProgressState>(INITIAL_PROGRESS);
  const progressRef = useRef<DownloadProgressState>(INITIAL_PROGRESS);
  const abortController = useRef<AbortController>(null);
  const { conversationId } = useConversation();

  // Create AbortController on mount
  useEffect(() => {
    const controller = new AbortController();
    abortController.current = controller;
    // Initialize progress ref with initial state
    progressRef.current = INITIAL_PROGRESS;
    return () => {
      controller.abort();
      abortController.current = null;
    };
  }, []); // Empty deps array - only run on mount/unmount

  // Start download when isStarted becomes true
  useEffect(() => {
    if (!isStarted) {
      setIsStarted(true);
      return;
    }

    if (!abortController.current) return;

    // Start download
    const download = async () => {
      try {
        await downloadFiles(conversationId, initialPath, {
          onProgress: (p) => {
            // Update both the ref and state
            progressRef.current = { ...p };
            setProgress((prev: DownloadProgressState) => ({ ...prev, ...p }));
          },
          signal: abortController.current!.signal,
        });
        onClose();
      } catch (error) {
        if (error instanceof Error && error.message === "Download cancelled") {
          onClose();
        } else {
          throw error;
        }
      }
    };
    download();
  }, [initialPath, onClose, isStarted]);

  // No longer need startDownload as it's handled in useEffect

  const cancelDownload = useCallback(() => {
    abortController.current?.abort();
  }, []);

  return {
    progress,
    cancelDownload,
  };
}
