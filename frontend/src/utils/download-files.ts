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
 * Creates a download link and triggers the download
 */
function triggerDownload(content: string, filename: string): void {
  const blob = new Blob([content], { type: "application/octet-stream" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.parentNode?.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Creates subdirectories and returns the final directory handle
 */
async function createSubdirectories(
  baseHandle: FileSystemDirectoryHandle,
  pathParts: string[],
): Promise<FileSystemDirectoryHandle> {
  return pathParts.reduce(async (promise, part) => {
    const handle = await promise;
    return handle.getDirectoryHandle(part, { create: true });
  }, Promise.resolve(baseHandle));
}

/**
 * Recursively gets all files in a directory
 */
async function getAllFiles(
  path: string,
  progress: DownloadProgress,
  options?: DownloadOptions,
): Promise<string[]> {
  const entries = await OpenHands.getFiles(path);

  // Process directories first to get total file count
  const processEntry = async (entry: string): Promise<string[]> => {
    console.log('getting files', entry);
    if (options?.signal?.aborted) {
      console.log('aborted');
      throw new Error("Download cancelled");
    }

    const fullPath = path + entry;
    if (entry.endsWith("/")) {
      // It's a directory, recursively get its files
      const subEntries = await OpenHands.getFiles(fullPath);
      const subFilesPromises = subEntries.map((subEntry) =>
        processEntry(subEntry),
      );
      const subFilesArrays = await Promise.all(subFilesPromises);
      return subFilesArrays.flat();
    }
    const newProgress = {
      ...progress,
      filesTotal: progress.filesTotal + 1,
    };
    options?.onProgress?.(newProgress);
    return [fullPath];
  };

  const filePromises = entries.map((entry) => processEntry(entry));
  const fileArrays = await Promise.all(filePromises);
  return fileArrays.flat();
}

/**
 * Process a batch of files
 */
async function processBatch(
  batch: string[],
  directoryHandle: FileSystemDirectoryHandle | null,
  progress: DownloadProgress,
  startTime: number,
  options?: DownloadOptions,
): Promise<void> {
  if (options?.signal?.aborted) {
    throw new Error("Download cancelled");
  }

  // Process files in the batch in parallel
  const batchPromises = batch.map(async (path) => {
    try {
      const newProgress = {
        ...progress,
        currentFile: path,
      };
      options?.onProgress?.(newProgress);

      const content = await OpenHands.getFile(path);

      if (directoryHandle) {
        // Save to the selected directory preserving structure
        const pathParts = path.split("/").filter(Boolean);
        const fileName = pathParts.pop() || "file";
        const dirHandle =
          pathParts.length > 0
            ? await createSubdirectories(directoryHandle, pathParts)
            : directoryHandle;

        // Create and write the file
        const fileHandle = await dirHandle.getFileHandle(fileName, {
          create: true,
        });
        const writable = await fileHandle.createWritable();
        await writable.write(content);
        await writable.close();
      } else {
        // Fallback: Download directly using <a> tag
        triggerDownload(content, path.split("/").pop() || "file");
      }

      // Update progress
      const contentSize = new Blob([content]).size;
      const newProgressWithStats = {
        ...progress,
        filesDownloaded: progress.filesDownloaded + 1,
        totalBytesDownloaded: progress.totalBytesDownloaded + contentSize,
      };
      newProgressWithStats.bytesDownloadedPerSecond =
        newProgressWithStats.totalBytesDownloaded /
        ((Date.now() - startTime) / 1000);
      options?.onProgress?.(newProgressWithStats);
    } catch (error) {
      throw new Error(
        `Failed to download file ${path}: ${error instanceof Error ? error.message : String(error)}`,
      );
    }
  });

  await Promise.all(batchPromises);
}

/**
 * Downloads files from the workspace one by one
 * @param initialPath Initial path to start downloading from. If not provided, downloads from root
 * @param options Download options including progress callback and abort signal
 */
export async function downloadFiles(
  initialPath?: string,
  options?: DownloadOptions,
): Promise<void> {
  const startTime = Date.now();
  const progress: DownloadProgress = {
    filesTotal: 0,
    filesDownloaded: 0,
    currentFile: "",
    totalBytesDownloaded: 0,
    bytesDownloadedPerSecond: 0,
  };

  try {
    // First, recursively get all files
    console.log('init path', initialPath);
    const files = await getAllFiles(initialPath || "", progress, options);
    console.log('files', files);

    // Create a directory picker if the browser supports it
    let directoryHandle: FileSystemDirectoryHandle | null = null;
    if ("showDirectoryPicker" in window) {
      try {
        directoryHandle = await window.showDirectoryPicker();
        console.log('got directoryHandle', directoryHandle);
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
          throw new Error("Download cancelled");
        }
        // Directory picker not supported or cancelled, will fall back to individual downloads
      }
    } else {
      console.log('no dir picker');
    }

    // Process files in parallel batches to avoid overwhelming the browser
    const BATCH_SIZE = 5;
    const batches = Array.from(
      { length: Math.ceil(files.length / BATCH_SIZE) },
      (_, i) => files.slice(i * BATCH_SIZE, (i + 1) * BATCH_SIZE),
    );

    // Process batches sequentially to maintain order and avoid overwhelming the browser
    await batches.reduce(
      (promise, batch) =>
        promise.then(() =>
          processBatch(batch, directoryHandle, progress, startTime, options),
        ),
      Promise.resolve(),
    );
  } catch (error) {
    if (error instanceof Error && error.message === "Download cancelled") {
      throw error;
    }
    // Re-throw with a more descriptive message
    throw new Error(
      `Failed to download files: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}
