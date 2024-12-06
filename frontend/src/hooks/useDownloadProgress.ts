import { useCallback, useRef, useState } from "react";
import { downloadFiles } from "#/utils/download-files";
import { DownloadProgress } from "#/components/shared/download-progress";

export function useDownloadProgress(initialPath: string | undefined, onClose: () => void) {
  const [progress, setProgress] = useState<DownloadProgress>({
    filesTotal: 0,
    filesDownloaded: 0,
    currentFile: "",
    totalBytesDownloaded: 0,
    bytesDownloadedPerSecond: 0,
  });

  const abortController = useRef(new AbortController());

  const startDownload = useCallback(async () => {
    if (!initialPath) return;

    try {
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
    abortController.current.abort();
  }, []);

  return {
    progress,
    startDownload,
    cancelDownload,
  };
}