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

    // Create a zip file using JSZip
    const JSZip = (await import("jszip")).default;
    const zip = new JSZip();

    // Download each file
    for (const path of files) {
      if (options?.signal?.aborted) {
        throw new Error("Download cancelled");
      }

      try {
        progress.currentFile = path;
        const content = await OpenHands.getFile(path);
        
        // Add file to zip, preserving directory structure
        zip.file(path, content);

        // Update progress
        progress.filesDownloaded++;
        progress.totalBytesDownloaded += new Blob([content]).size;
        progress.bytesDownloadedPerSecond = progress.totalBytesDownloaded / ((Date.now() - startTime) / 1000);
        options?.onProgress?.(progress);
      } catch (error) {
        console.error(`Error downloading file ${path}:`, error);
      }
    }

    if (options?.signal?.aborted) {
      throw new Error("Download cancelled");
    }

    // Generate and download the zip file
    const blob = await zip.generateAsync({ type: "blob" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", initialPath ? `${initialPath.replace(/\/$/, "")}.zip` : "workspace.zip");
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    if (error instanceof Error && error.message === "Download cancelled") {
      throw error;
    }
    console.error("Download error:", error);
    throw new Error("Failed to download files");
  }
}