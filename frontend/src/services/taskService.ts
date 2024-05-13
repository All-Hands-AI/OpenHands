export type Task = {
  id: string;
  goal: string;
  subtasks: Task[];
  state: TaskState;
};

export enum TaskState {
  OPEN_STATE = "open",
  COMPLETED_STATE = "completed",
  ABANDONED_STATE = "abandoned",
  IN_PROGRESS_STATE = "in_progress",
  VERIFIED_STATE = "verified",
}

export async function getRootTask(): Promise<Task | undefined> {
  const headers = new Headers({
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });
  const res = await fetch("/api/root_task", { headers });
  if (res.status !== 200 && res.status !== 204) {
    return undefined;
  }
  const data = (await res.json()) as Task;
  return data;
}
