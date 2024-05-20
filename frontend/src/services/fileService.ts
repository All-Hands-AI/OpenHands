import { request } from "./api";

export async function selectFile(file: string): Promise<string> {
  const data = await request(`/api/select-file?file=${file}`);
  return data.code as string;
}

export async function uploadFiles(files: FileList) {
  const formData = new FormData();
  for (let i = 0; i < files.length; i += 1) {
    formData.append("files", files[i]);
  }

  await request("/api/upload-files", {
    method: "POST",
    body: formData,
  });
}

export async function listFiles(path: string = "/"): Promise<string[]> {
  const data = await request(`/api/list-files?path=${path}`);
  return data as string[];
}
