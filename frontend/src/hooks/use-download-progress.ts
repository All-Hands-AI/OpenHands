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

  // Create a new AbortController and start the download when the hook is initialized
  useEffect(() => {
    console.log('Download effect starting, path:', initialPath);
    const controller = new AbortController();
    abortController.current = controller;

    // Start download immediately
    const download = async () => {
      try {
        console.log('Starting download...');
        await downloadFiles(initialPath, {
          onProgress: (p) => {
            console.log('Progress:', p);
            setProgress(p);
          },
          signal: controller.signal,
        });
        console.log('Download completed');
        onClose();
      } catch (error) {
        console.log('Download error:', error);
        if (error instanceof Error && error.message === "Download cancelled") {
          onClose();
        } else {
          throw error;
        }
      }
    };
    download();

    return () => {
      console.log('Download effect cleanup');
      controller.abort();
      abortController.current = undefined;
    };
  }, [initialPath, onClose]);

  // No longer need startDownload as it's handled in useEffect

  const cancelDownload = useCallback(() => {
    abortController.current?.abort();
  }, []);

  return {
    progress,
    cancelDownload,
  };
}
