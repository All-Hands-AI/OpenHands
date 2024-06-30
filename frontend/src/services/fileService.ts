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

export async function uploadFiles(files: FileList): Promise<void> {
  try {
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append("files", file));

    await request("/api/upload-files", {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    toast.error(
      "file-upload-error",
      translate(I18nKey.FILE_SERVICE$UPLOAD_FILES_ERROR),
    );
    throw error;
  }
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
