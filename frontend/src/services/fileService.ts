import { request } from "./api";
import toast from "#/utils/toast";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export async function selectFile(file: string): Promise<string> {
  const { t } = useTranslation();
  try {
    const data = await request(`/api/select-file?file=${encodeURIComponent(file)}`);
    if (typeof data.code !== 'string') {
      throw new Error('Invalid response format: code is not a string');
    }
    return data.code;
  } catch (error) {
    console.error('Error selecting file:', error);
    toast.error(t(I18nKey.FILE_SERVICE$SELECT_FILE_ERROR), 'File Selection Error');
    throw error;
  }
}

export async function uploadFiles(files: FileList): Promise<void> {
  const { t } = useTranslation();
  try {
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append("files", file));

    await request("/api/upload-files", {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    console.error('Error uploading files:', error);
    toast.error(t(I18nKey.FILE_SERVICE$UPLOAD_FILES_ERROR), 'Upload Error');
    throw error;
  }
}

export async function listFiles(path: string = "/"): Promise<string[]> {
  const { t } = useTranslation();
  try {
    const data = await request(`/api/list-files?path=${encodeURIComponent(path)}`);
    if (!Array.isArray(data)) {
      throw new Error('Invalid response format: data is not an array');
    }
    return data;
  } catch (error) {
    console.error('Error listing files:', error);
    toast.error(t(I18nKey.FILE_SERVICE$LIST_FILES_ERROR), 'File List Error');
    throw error;
  }
}

export async function saveFile(filePath: string, content: string): Promise<void> {
  const { t } = useTranslation();
  try {
    if (!filePath || filePath.includes('..')) {
      toast.error(t(I18nKey.FILE_SERVICE$INVALID_FILE_PATH));
      throw new Error('Invalid file path');
    }

    await request("/api/save-file", {
      method: "POST",
      body: JSON.stringify({ filePath, content }),
      headers: {
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    console.error('Error saving file:', error);
    toast.error(t(I18nKey.FILE_SERVICE$SAVE_FILE_ERROR), 'File Save Error');
    throw error;
  }
}