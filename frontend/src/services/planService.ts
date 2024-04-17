export type Plan = {
  mainGoal: string | undefined;
  task: Task;
};

export type Task = {
  id: string;
  goal: string;
  parent: "Task | None";
  subtasks: Task[];
  state: string;
};

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
