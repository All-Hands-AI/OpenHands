export type Plan = {
  mainGoal: string | undefined;
  task: Task;
};

export type Task = {
  id: string;
  goal: string;
  parent: "Task | None";
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

export async function getPlan(): Promise<Plan | undefined> {
  const headers = new Headers({
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });
  const res = await fetch("/api/plan", { headers });
  if (res.status !== 200) {
    return undefined;
  }
  const data = await res.json();
  return JSON.parse(data) as Plan;
}
