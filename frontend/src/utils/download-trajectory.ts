import { downloadJSON } from "./download-json";

function isSaveFilePickerSupported(): boolean {
  return typeof window !== "undefined" && "showSaveFilePicker" in window;
}

export async function downloadTrajectory(
  conversationId: string,
  data: unknown[] | null,
): Promise<void> {
  // Ensure data is an object for downloadJSON
  const jsonData = data || {};

  if (!isSaveFilePickerSupported()) {
    // Fallback for browsers that don't support File System Access API (Safari, Firefox)
    // This method dumps the JSON data right into the download folder
    downloadJSON(jsonData as object, `trajectory-${conversationId}.json`);
    return;
  }

  try {
    const options: SaveFilePickerOptions = {
      suggestedName: `trajectory-${conversationId}.json`,
      types: [
        {
          description: "JSON File", // This is a file type description, not user-facing text
          accept: {
            "application/json": [".json"],
          },
        },
      ],
    };

    const fileHandle = await window.showSaveFilePicker(options);
    const writable = await fileHandle.createWritable();
    await writable.write(JSON.stringify(data, null, 2));
    await writable.close();
  } catch (error) {
    // If an error occurs, fall back to the downloadJSON method
    if (error instanceof Error && error.name !== "AbortError") {
      downloadJSON(jsonData as object, `trajectory-${conversationId}.json`);
    }
  }
}
