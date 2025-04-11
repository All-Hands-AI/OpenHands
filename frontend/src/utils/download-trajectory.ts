function isSaveFilePickerSupported(): boolean {
  return typeof window !== "undefined" && "showSaveFilePicker" in window;
}

export async function downloadTrajectory(
  conversationId: string,
  data: unknown[] | null,
): Promise<void> {
  if (!isSaveFilePickerSupported()) {
    throw new Error(
      "Your browser doesn't support downloading files. Please use Chrome, Edge, or another browser that supports the File System Access API.",
    );
  }
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
}
