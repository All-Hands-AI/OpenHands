import i18next from "i18next";
import { I18nKey } from "#/i18n/declaration";
import { request } from "./api";

const translate = (key: I18nKey) => i18next.t(key);

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

  // Add skippedFilesCount to formData
  formData.append("skippedFilesCount", skippedFiles.length.toString());

  // Add uploadedFilesCount to formData
  formData.append("uploadedFilesCount", uploadedCount.toString());

  const response = await request("/api/upload-files", {
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
  let url = "/api/list-files";
  if (path) {
    url = `/api/list-files?path=${encodeURIComponent(path)}`;
  }
  const data = await request(url);
  if (!Array.isArray(data)) {
    throw new Error("Invalid response format: data is not an array");
  }
  return data;
}

export async function saveFile(
  filePath: string,
  content: string,
): Promise<void> {
  if (!filePath || filePath.includes("..")) {
    throw new Error(translate(I18nKey.FILE_SERVICE$INVALID_FILE_PATH));
  }

  await request("/api/save-file", {
    method: "POST",
    body: JSON.stringify({ filePath, content }),
    headers: {
      "Content-Type": "application/json",
    },
  });
}
