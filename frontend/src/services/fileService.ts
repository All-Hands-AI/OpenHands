export type WorkspaceFile = {
  name: string;
  children?: WorkspaceFile[];
};

export async function selectFile(file: string): Promise<string> {
  const res = await fetch(`/api/select-file?file=${file}`);
  const data = await res.json();
  if (res.status !== 200) {
    throw new Error(data.error);
  }
  return data.code as string;
}

export async function getWorkspace(): Promise<WorkspaceFile> {
  const res = await fetch("/api/refresh-files");
  const data = await res.json();
  return data as WorkspaceFile;
}
