import { useCallback, useEffect, useRef, useState } from "react";
import { downloadFiles } from "#/utils/download-files";
import { DownloadProgress } from "#/components/shared/download-progress";

export const INITIAL_PROGRESS: DownloadProgress = {
  filesTotal: 0,
  filesDownloaded: 0,
  currentFile: "",
  totalBytesDownloaded: 0,
  bytesDownloadedPerSecond: 0,
  isDiscoveringFiles: true,
};

export function useDownloadProgress(initialPath: string | undefined, onClose: () => void) {
  const [progress, setProgress] = useState<DownloadProgress>(INITIAL_PROGRESS);

  const abortController = useRef<AbortController>();

  useEffect(() => {
    abortController.current = new AbortController();
    return () => abortController.current?.abort();
  }, []);

  const startDownload = useCallback(async () => {
    try {
      if (!abortController.current) return;
      await downloadFiles(initialPath, {
        onProgress: setProgress,
        signal: abortController.current.signal,
      });
      onClose();
    } catch (error) {
      if (error instanceof Error && error.message === "Download cancelled") {
        onClose();
      } else {
        throw error;
      }
    }
  }, [initialPath, onClose]);

  const cancelDownload = useCallback(() => {
    abortController.current?.abort();
  }, []);

  return {
    progress,
    startDownload,
    cancelDownload,
  };
}
