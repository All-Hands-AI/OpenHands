import { useEffect } from "react";
import { useDownloadProgress } from "#/hooks/useDownloadProgress";
import { DownloadProgress } from "./download-progress";

interface DownloadModalProps {
  initialPath: string;
  onClose: () => void;
}

export function DownloadModal({ initialPath, onClose }: DownloadModalProps) {
  const { progress, startDownload, cancelDownload } = useDownloadProgress(
    initialPath,
    onClose
  );

  useEffect(() => {
    startDownload();
  }, [startDownload]);

  return (
    <DownloadProgress
      progress={progress}
      onCancel={cancelDownload}
      onClose={onClose}
    />
  );
}