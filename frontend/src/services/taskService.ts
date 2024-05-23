import { request } from "./api";

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
  const res = await request("/api/root_task");
  return res as Task;
}
