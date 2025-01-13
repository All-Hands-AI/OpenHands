import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export interface DownloadProgressState {
  filesTotal: number;
  filesDownloaded: number;
  currentFile: string;
  totalBytesDownloaded: number;
  bytesDownloadedPerSecond: number;
  isDiscoveringFiles: boolean;
}

interface DownloadProgressProps {
  progress: DownloadProgressState;
  onCancel: () => void;
}

export function DownloadProgress({
  progress,
  onCancel,
}: DownloadProgressProps) {
  const { t } = useTranslation();
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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-20">
      <div className="bg-[#1C1C1C] rounded-lg p-6 max-w-md w-full mx-4 border border-[#525252]">
        <div className="mb-4">
          <h3 className="text-lg font-semibold mb-2 text-white">
            {progress.isDiscoveringFiles
              ? t(I18nKey.DOWNLOAD$PREPARING)
              : t(I18nKey.DOWNLOAD$DOWNLOADING)}
          </h3>
          <p className="text-sm text-gray-400 truncate">
            {progress.isDiscoveringFiles
              ? t(I18nKey.DOWNLOAD$FOUND_FILES, { count: progress.filesTotal })
              : progress.currentFile}
          </p>
        </div>

        <div className="mb-4">
          <div className="h-2 bg-[#2C2C2C] rounded-full overflow-hidden">
            {progress.isDiscoveringFiles ? (
              <div
                className="h-full bg-blue-500 animate-pulse"
                style={{ width: "100%" }}
              />
            ) : (
              <div
                className="h-full bg-blue-500 transition-all duration-300"
                style={{
                  width: `${(progress.filesDownloaded / progress.filesTotal) * 100}%`,
                }}
              />
            )}
          </div>
        </div>

        <div className="flex justify-between text-sm text-gray-400">
          <span>
            {progress.isDiscoveringFiles
              ? t(I18nKey.DOWNLOAD$SCANNING)
              : t(I18nKey.DOWNLOAD$FILES_PROGRESS, {
                  downloaded: progress.filesDownloaded,
                  total: progress.filesTotal,
                })}
          </span>
          {!progress.isDiscoveringFiles && (
            <span>{formatBytes(progress.bytesDownloadedPerSecond)}/s</span>
          )}
        </div>

        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            {t(I18nKey.DOWNLOAD$CANCEL)}
          </button>
        </div>
      </div>
    </div>
  );
}
