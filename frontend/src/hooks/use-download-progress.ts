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
  const [isStarted, setIsStarted] = useState(false);
  const [progress, setProgress] = useState<DownloadProgress>(INITIAL_PROGRESS);

  const abortController = useRef<AbortController>();

  // Create AbortController on mount
  useEffect(() => {
    console.log('Creating AbortController');
    const controller = new AbortController();
    abortController.current = controller;
    return () => {
      console.log('Cleaning up AbortController');
      controller.abort();
      abortController.current = undefined;
    };
  }, []); // Empty deps array - only run on mount/unmount

  // Start download when isStarted becomes true
  useEffect(() => {
    if (!isStarted) {
      setIsStarted(true);
      return;
    }

    console.log('Download effect starting, path:', initialPath);
    if (!abortController.current) return;

    // Start download
    const download = async () => {
      try {
        console.log('Starting download...');
        await downloadFiles(initialPath, {
          onProgress: (p) => {
            console.log('Progress:', p);
            setProgress(p);
          },
          signal: abortController.current!.signal,
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
