import { request } from "./api";

export type WorkspaceFile = {
  name: string;
  children?: WorkspaceFile[];
};

export async function selectFile(file: string): Promise<string> {
  const res = await request(`/api/select-file?file=${file}`);
  return res.code;
}

export async function uploadFile(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  await request("/api/upload-file", {
    method: "POST",
    body: formData,
  });
}

export async function getWorkspace(): Promise<WorkspaceFile> {
  const res = await request("/api/list-files");
  const wsFile = {children: []};
  wsFile.children = res.map(f => {name: f});
  return wsFile;
}

export async function listFiles(basePath: string = '/'): Promise<string[]> {
  const res = await request(`/api/list-files?path=${basePath}`);
  return res;
}
