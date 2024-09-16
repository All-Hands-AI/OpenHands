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
  error?: string;
}

export async function uploadFiles(files: FileList): Promise<UploadResult> {
  const formData = new FormData();
  const skippedFiles: Array<{ name: string; reason: string }> = [];

  let uploadedCount = 0;

  for (let i = 0; i < files.length; i += 1) {
    const file = files[i];

    if (
      file.name.includes("..") ||
      file.name.includes("/") ||
      file.name.includes("\\")
    ) {
      skippedFiles.push({
        name: file.name,
        reason: "Invalid file name",
      });
    } else {
      formData.append("files", file);
      uploadedCount += 1;
    }
  }

  formData.append("skippedFilesCount", skippedFiles.length.toString());
  formData.append("uploadedFilesCount", uploadedCount.toString());

  const response = await request("http://localhost:3000/api/upload-files", {
    method: "POST",
    body: formData,
  });

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
}

export async function listFiles(
  path: string | undefined = undefined,
): Promise<string[]> {
  let url = "http://localhost:3000/api/list-files";
  if (path) {
    url = `http://localhost:3000/api/list-files?path=${encodeURIComponent(path)}`;
  }
  const data = await request(url);
  if (!Array.isArray(data)) {
    throw new Error("Invalid response format: data is not an array");
  }
  return data;
}
