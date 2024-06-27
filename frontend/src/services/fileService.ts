import { request } from "./api";

export async function selectFile(file: string): Promise<string> {
  const encodedFile = encodeURIComponent(file);
  const data = await request(`/api/select-file?file=${encodedFile}`);
  return data.code as string;
}

interface UploadResult {
  message: string;
  uploadedFiles: string[];
  skippedFiles: Array<{ name: string; reason: string }>;
}

export async function uploadFiles(files: FileList): Promise<UploadResult> {
  const formData = new FormData();
  const skippedFiles: Array<{ name: string; reason: string }> = [];

  for (let i = 0; i < files.length; i += 1) {
    const file = files[i];
    console.log(`Processing file: ${file.name}`);

    if (
      file.name.includes("..") ||
      file.name.includes("/") ||
      file.name.includes("\\")
    ) {
      console.log(`Skipping file due to invalid name: ${file.name}`);
      skippedFiles.push({
        name: file.name,
        reason: "Invalid file name",
      });
    } else {
      console.log(`Adding file to formData: ${file.name}`);
      formData.append("files", file);
    }
  }

  try {
    console.log("Sending upload request");
    const response = await request("/api/upload-files", {
      method: "POST",
      body: formData,
    });

    console.log("Upload response:", response);

    if (
      typeof response.message !== "string" ||
      !Array.isArray(response.uploaded_files) ||
      !Array.isArray(response.skipped_files)
    ) {
      throw new Error("Unexpected response structure from server");
    }

    return {
      message: response.message,
      uploadedFiles: response.uploaded_files,
      skippedFiles: [...skippedFiles, ...response.skipped_files],
    };
  } catch (error) {
    console.error("Error during file upload:", error);
    throw error; // Re-throw the error to be handled by the caller
  }
}

export async function listFiles(path: string = "/"): Promise<string[]> {
  try {
    const encodedPath = encodeURIComponent(path);
    const data = await request(`/api/list-files?path=${encodedPath}`);
    return data as string[];
  } catch (error) {
    console.error(`Error listing files for path ${path}:`, error);
    // Return an empty array if the directory doesn't exist
    return [];
  }
}
