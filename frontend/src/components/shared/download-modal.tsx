import { useEffect, useState } from "react";
import { useDownloadProgress } from "#/hooks/use-download-progress";
import { DownloadProgress } from "./download-progress";

interface DownloadModalProps {
  initialPath: string;
  onClose: () => void;
  isOpen: boolean;
}

export function DownloadModal({ initialPath, onClose, isOpen }: DownloadModalProps) {
  console.log('DownloadModal rendering, path:', initialPath);

  useEffect(() => {
    console.log('DownloadModal mounted');
    return () => console.log('DownloadModal unmounting');
  }, []);

  const { progress, cancelDownload } = useDownloadProgress(
    initialPath,
    onClose
  );

  if (!isOpen) return null;

  return (
    <DownloadProgress
      progress={progress}
      onCancel={cancelDownload}
      onClose={onClose}
    />
  );
}
