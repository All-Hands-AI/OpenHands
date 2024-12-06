
import { useDownloadProgress } from "#/hooks/use-download-progress";
import { DownloadProgress } from "./download-progress";

interface DownloadModalProps {
  initialPath: string;
  onClose: () => void;
  isOpen: boolean;
}

export function DownloadModal({
  initialPath,
  onClose,
  isOpen,
}: DownloadModalProps) {
  if (!isOpen) return null;

  return <ActiveDownload initialPath={initialPath} onClose={onClose} />;
}

function ActiveDownload({
  initialPath,
  onClose,
}: {
  initialPath: string;
  onClose: () => void;
}) {
  const { progress, cancelDownload } = useDownloadProgress(
    initialPath,
    onClose,
  );

  return (
    <DownloadProgress
      progress={progress}
      onCancel={cancelDownload}
      onClose={onClose}
    />
  );
}
