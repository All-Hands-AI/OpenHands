import { request } from "./api";
import toast from "#/utils/toast";

export async function selectFile(file: string): Promise<string> {
  try {
    const data = await request(`/api/select-file?file=${encodeURIComponent(file)}`);
    if (typeof data.code !== 'string') {
      throw new Error('Invalid response format: code is not a string');
    }
    return data.code;
  } catch (error) {
    console.error('Error selecting file:', error);
    toast.error('Failed to select file. Please try again.', 'File Selection Error');
    throw error;
  }
}

export async function uploadFiles(files: FileList): Promise<void> {
  try {
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append("files", file));

    await request("/api/upload-files", {
      method: "POST",
      body: formData,
    });
  } catch (error) {
    console.error('Error uploading files:', error);
    toast.error('Failed to upload files. Please try again.', 'Upload Error');
    throw error;
  }
}

export async function listFiles(path: string = "/"): Promise<string[]> {
  try {
    const data = await request(`/api/list-files?path=${encodeURIComponent(path)}`);
    if (!Array.isArray(data)) {
      throw new Error('Invalid response format: data is not an array');
    }
    return data;
  } catch (error) {
    console.error('Error listing files:', error);
    toast.error('Failed to list files. Please try again.', 'File List Error');
    throw error;
  }
}

export async function saveFile(filePath: string, content: string): Promise<void> {
  try {
    await request("/api/save-file", {
      method: "POST",
      body: JSON.stringify({ filePath, content }),
      headers: {
        "Content-Type": "application/json",
      },
    });
  } catch (error) {
    console.error('Error saving file:', error);
    toast.error('Failed to save file. Please try again.', 'File Save Error');
    throw error;
  }
}