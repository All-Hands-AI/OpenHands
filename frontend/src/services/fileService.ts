export type WorkspaceFile = {
  name: string;
  children?: WorkspaceFile[];
};

export async function selectFile(file: string): Promise<string> {
  const res = await fetch(`/api/select-file?file=${file}`);
  return (await JSON.parse(await res.json()).code) as string;
}

export async function getWorkspace(): Promise<WorkspaceFile> {
  const res = await fetch("/api/refresh-files");
  return (await JSON.parse(await res.json())) as WorkspaceFile;
}
