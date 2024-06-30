import i18next from "i18next";
import { I18nKey } from "#/i18n/declaration";
import toast from "#/utils/toast";
import { request } from "./api";

const translate = (key: I18nKey) => i18next.t(key);

export async function selectFile(file: string): Promise<string> {
  try {
    const data = await request(
      `/api/select-file?file=${encodeURIComponent(file)}`,
    );
    if (typeof data.code !== "string") {
      throw new Error("Invalid response format: code is not a string");
    }
    return data.code;
  } catch (error) {
    toast.error(
      "file-selection-error",
      translate(I18nKey.FILE_SERVICE$SELECT_FILE_ERROR),
    );
    throw error;
  }
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

export async function listFiles(path: string = "/"): Promise<string[]> {
  try {
    const data = await request(
      `/api/list-files?path=${encodeURIComponent(path)}`,
    );
    if (!Array.isArray(data)) {
      throw new Error("Invalid response format: data is not an array");
    }
    return data;
  } catch (error) {
    toast.error(
      "file-list-error",
      translate(I18nKey.FILE_SERVICE$LIST_FILES_ERROR),
    );
    throw error;
  }
}

export async function saveFile(
  filePath: string,
  content: string,
): Promise<void> {
  try {
    if (!filePath || filePath.includes("..")) {
      toast.error(
        "file-save-error",
        translate(I18nKey.FILE_SERVICE$INVALID_FILE_PATH),
      );
      throw new Error("Invalid file path");
    }

    await request("/api/save-file", {
      method: "POST",
      body: JSON.stringify({ filePath, content }),
      headers: {
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    toast.error(
      "file-save-error",
      translate(I18nKey.FILE_SERVICE$SAVE_FILE_ERROR),
    );
    throw error;
  }
}
