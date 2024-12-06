import OpenHands from "#/api/open-hands";

interface DownloadProgress {
  filesTotal: number;
  filesDownloaded: number;
  currentFile: string;
  totalBytesDownloaded: number;
  bytesDownloadedPerSecond: number;
  isDiscoveringFiles: boolean;
}

interface DownloadOptions {
  onProgress?: (progress: DownloadProgress) => void;
  signal?: AbortSignal;
}

/**
 * Checks if the File System Access API is supported
 */
function isFileSystemAccessSupported(): boolean {
  return "showDirectoryPicker" in window;
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
    progress.filesTotal += 1;
    options?.onProgress?.({
      ...progress,
      currentFile: fullPath,
      isDiscoveringFiles: true,
    });
    return [fullPath];
  };

  const filePromises = entries.map((entry) => processEntry(entry));
  const fileArrays = await Promise.all(filePromises);
  
  // Signal that file discovery is complete
  progress.isDiscoveringFiles = false;
  options?.onProgress?.({ ...progress });
  
  return fileArrays.flat();
}

/**
 * Process a batch of files
 */
async function processBatch(
  batch: string[],
  directoryHandle: FileSystemDirectoryHandle,
  progress: DownloadProgress,
  startTime: number,
  completedFiles: number,
  totalBytes: number,
  options?: DownloadOptions,
): Promise<{ newCompleted: number; newBytes: number }> {
  if (options?.signal?.aborted) {
    throw new Error("Download cancelled");
  }

  // Process files in the batch in parallel
  const results = await Promise.all(batch.map(async (path) => {
    try {
      const newProgress = {
        ...progress,
        currentFile: path,
        isDiscoveringFiles: false,
        filesDownloaded: completedFiles,
        totalBytesDownloaded: totalBytes,
        bytesDownloadedPerSecond: totalBytes / ((Date.now() - startTime) / 1000)
      };
      options?.onProgress?.(newProgress);

      const content = await OpenHands.getFile(path);

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

      // Return the size of this file
      return new Blob([content]).size;
    } catch (error) {
      console.error(`Error processing file ${path}:`, error);
      return 0;
    }
  }));

  // Calculate batch totals
  const batchBytes = results.reduce((sum, size) => sum + size, 0);
  const newTotalBytes = totalBytes + batchBytes;
  const newCompleted = completedFiles + results.filter(size => size > 0).length;

  // Update progress with batch results
  const updatedProgress = {
    ...progress,
    filesDownloaded: newCompleted,
    totalBytesDownloaded: newTotalBytes,
    bytesDownloadedPerSecond: newTotalBytes / ((Date.now() - startTime) / 1000),
    isDiscoveringFiles: false
  };
  Object.assign(progress, updatedProgress);
  options?.onProgress?.(updatedProgress);

  return {
    newCompleted,
    newBytes: newTotalBytes
  };
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
    isDiscoveringFiles: true,
  };

  try {
    // Check if File System Access API is supported
    if (!isFileSystemAccessSupported()) {
      throw new Error(
        "Your browser doesn't support downloading folders. Please use Chrome, Edge, or another browser that supports the File System Access API."
      );
    }

    // Show directory picker first
    let directoryHandle: FileSystemDirectoryHandle;
    try {
      console.log('Showing directory picker...');
      const pickerOpts = {
        mode: 'readwrite',
        startIn: 'downloads',
      };
      directoryHandle = await window.showDirectoryPicker(pickerOpts);
      console.log('got directoryHandle', directoryHandle);
    } catch (error) {
      console.log('Directory picker error:', error);
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("Download cancelled");
      }
      if (error instanceof Error && error.name === "SecurityError") {
        throw new Error("Permission denied. Please allow access to the download location when prompted.");
      }
      throw new Error("Failed to select download location. Please try again.");
    }

    // Then recursively get all files
    console.log('init path', initialPath);
    const files = await getAllFiles(initialPath || "", progress, options);
    console.log('files', files);

    // Set isDiscoveringFiles to false now that we have the full list
    options?.onProgress?.({
      ...progress,
      isDiscoveringFiles: false,
    });

    // Verify we still have permission after the potentially long file scan
    try {
      // Try to create a test file to verify permissions
      const testHandle = await directoryHandle.getFileHandle('.openhands-test', { create: true });
      await testHandle.remove();
    } catch (error) {
      if (error instanceof Error && error.message.includes('User activation is required')) {
        // Ask for permission again
        try {
          console.log('Re-showing directory picker...');
          const pickerOpts = {
            mode: 'readwrite',
            startIn: 'downloads',
          };
          directoryHandle = await window.showDirectoryPicker(pickerOpts);
          console.log('got new directoryHandle after timeout');
        } catch (error) {
          console.log('Re-prompt error:', error);
          if (error instanceof Error && error.name === "AbortError") {
            throw new Error("Download cancelled");
          }
          if (error instanceof Error && error.name === "SecurityError") {
            throw new Error("Permission denied. Please allow access to the download location when prompted.");
          }
          throw new Error("Failed to select download location. Please try again.");
        }
      } else {
        throw error;
      }
    }

    // Process files in parallel batches to avoid overwhelming the browser
    const BATCH_SIZE = 5;
    const batches = Array.from(
      { length: Math.ceil(files.length / BATCH_SIZE) },
      (_, i) => files.slice(i * BATCH_SIZE, (i + 1) * BATCH_SIZE),
    );

    // Keep track of completed files across all batches
    let completedFiles = 0;
    let totalBytesDownloaded = 0;

    // Process batches sequentially to maintain order and avoid overwhelming the browser
    await batches.reduce(
      (promise, batch) =>
        promise.then(async () => {
          const { newCompleted, newBytes } = await processBatch(
            batch,
            directoryHandle,
            progress,
            startTime,
            completedFiles,
            totalBytesDownloaded,
            options
          );
          completedFiles = newCompleted;
          totalBytesDownloaded = newBytes;
        }),
      Promise.resolve(),
    );
  } catch (error) {
    if (error instanceof Error && error.message === "Download cancelled") {
      throw error;
    }
    // Re-throw the error as is if it's already a user-friendly message
    if (error instanceof Error && (
      error.message.includes("browser doesn't support") ||
      error.message.includes("Failed to select") ||
      error.message === "Download cancelled"
    )) {
      throw error;
    }
    
    // Otherwise, wrap it with a generic message
    throw new Error(
      `Failed to download files: ${error instanceof Error ? error.message : String(error)}`,
    );
  }
}