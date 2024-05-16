import { request } from "./api";

export async function selectFile(file: string): Promise<string> {
  const res = await request(`/api/select-file?file=${file}`);
  return res.code;
}

export async function uploadFiles(files: FileList) {
  const formData = new FormData();
  for (let i = 0; i < files.length; i += 1) {
    formData.append("files", files[i]);
  }

  const res = await request("/api/upload-files", {
    method: "POST",
    body: formData,
  });

  const data = await res.json();

  if (res.status !== 200) {
    throw new Error(data.error || "Failed to upload files.");
  }
}

export async function listFiles(basePath: string = '/'): Promise<string[]> {
  const res = await request(`/api/list-files?path=${basePath}`);
  return res as string[];
}
