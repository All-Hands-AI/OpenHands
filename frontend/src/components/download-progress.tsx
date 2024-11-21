import { useCallback, useEffect, useRef, useState } from "react";
import { downloadFiles } from "#/utils/download-files";

interface DownloadProgressProps {
  initialPath?: string;
  onClose: () => void;
}

export function DownloadProgress({
  initialPath,
  onClose,
}: DownloadProgressProps) {
  const [progress, setProgress] = useState({
    filesTotal: 0,
    filesDownloaded: 0,
    currentFile: "",
    totalBytesDownloaded: 0,
    bytesDownloadedPerSecond: 0,
  });

  const abortController = useRef(new AbortController());

  const handleDownload = useCallback(async () => {
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
        // Let the error propagate to the parent component
        throw error;
      }
    }
  }, [initialPath, onClose]);

  useEffect(() => {
    handleDownload();
    return () => abortController.current.abort();
  }, [handleDownload]);

  const formatBytes = (bytes: number) => {
    const units = ["B", "KB", "MB", "GB"];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex += 1;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="mb-4">
          <h3 className="text-lg font-semibold mb-2">Downloading Files</h3>
          <p className="text-sm text-gray-600 truncate">
            {progress.currentFile}
          </p>
        </div>

        <div className="mb-4">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{
                width: `${(progress.filesDownloaded / progress.filesTotal) * 100}%`,
              }}
            />
          </div>
        </div>

        <div className="flex justify-between text-sm text-gray-600">
          <span>
            {progress.filesDownloaded} of {progress.filesTotal} files
          </span>
          <span>{formatBytes(progress.bytesDownloadedPerSecond)}/s</span>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={() => abortController.current.abort()}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
