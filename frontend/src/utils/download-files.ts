import OpenHands from "#/api/open-hands";

interface DownloadProgress {
  filesTotal: number;
  filesDownloaded: number;
  currentFile: string;
  totalBytesDownloaded: number;
  bytesDownloadedPerSecond: number;
}

interface DownloadOptions {
  onProgress?: (progress: DownloadProgress) => void;
  signal?: AbortSignal;
}

/**
 * Recursively gets all files in a directory
 */
async function getAllFiles(
  path: string,
  progress: DownloadProgress,
  options?: DownloadOptions
): Promise<string[]> {
  const files: string[] = [];
  const entries = await OpenHands.getFiles(path);

  for (const entry of entries) {
    if (options?.signal?.aborted) {
      throw new Error("Download cancelled");
    }

    if (entry.endsWith("/")) {
      // It's a directory, recursively get its files
      const subFiles = await getAllFiles(entry, progress, options);
      files.push(...subFiles);
    } else {
      files.push(entry);
      progress.filesTotal++;
      options?.onProgress?.(progress);
    }
  }

  return files;
}

/**
 * Downloads files from the workspace one by one
 * @param initialPath Initial path to start downloading from. If not provided, downloads from root
 * @param options Download options including progress callback and abort signal
 */
export async function downloadFiles(initialPath?: string, options?: DownloadOptions): Promise<void> {
  const startTime = Date.now();
  const progress: DownloadProgress = {
    filesTotal: 0,
    filesDownloaded: 0,
    currentFile: "",
    totalBytesDownloaded: 0,
    bytesDownloadedPerSecond: 0
  };

  try {
    // First, recursively get all files
    const files = await getAllFiles(initialPath || "", progress, options);

    // Create a directory picker if the browser supports it
    let directoryHandle: FileSystemDirectoryHandle | null = null;
    if ('showDirectoryPicker' in window) {
      try {
        directoryHandle = await window.showDirectoryPicker();
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          throw new Error("Download cancelled");
        }
        console.warn('Directory picker not supported or cancelled, falling back to individual downloads');
      }
    }

    // Download each file
    for (const path of files) {
      if (options?.signal?.aborted) {
        throw new Error("Download cancelled");
      }

      try {
        progress.currentFile = path;
        const content = await OpenHands.getFile(path);
        
        if (directoryHandle) {
          // Save to the selected directory preserving structure
          const pathParts = path.split('/').filter(Boolean);
          let currentHandle = directoryHandle;

          // Create subdirectories as needed
          for (let i = 0; i < pathParts.length - 1; i++) {
            currentHandle = await currentHandle.getDirectoryHandle(pathParts[i], { create: true });
          }

          // Create and write the file
          const fileName = pathParts[pathParts.length - 1];
          const fileHandle = await currentHandle.getFileHandle(fileName, { create: true });
          const writable = await fileHandle.createWritable();
          await writable.write(content);
          await writable.close();
        } else {
          // Fallback: Download directly using <a> tag
          const blob = new Blob([content], { type: 'application/octet-stream' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = path.split('/').pop() || 'file';
          document.body.appendChild(link);
          link.click();
          link.parentNode?.removeChild(link);
          URL.revokeObjectURL(url);
        }

        // Update progress
        progress.filesDownloaded++;
        progress.totalBytesDownloaded += new Blob([content]).size;
        progress.bytesDownloadedPerSecond = progress.totalBytesDownloaded / ((Date.now() - startTime) / 1000);
        options?.onProgress?.(progress);
      } catch (error) {
        console.error(`Error downloading file ${path}:`, error);
      }
    }
  } catch (error) {
    if (error instanceof Error && error.message === "Download cancelled") {
      throw error;
    }
    console.error("Download error:", error);
    throw new Error("Failed to download files");
  }
}