export interface TaskItem {
  taskId: string;
  title: string;
  description: string;
}

export interface RepositoryTaskGroup {
  title: string;
  tasks: TaskItem[];
}
