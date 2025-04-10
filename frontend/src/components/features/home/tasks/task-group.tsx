import { TaskCard } from "./task-card";
import { TaskItemTitle } from "./task-item-title";
import { TaskItem } from "./task.types";

interface TaskGroupProps {
  title: string;
  tasks: TaskItem[];
}

export function TaskGroup({ title, tasks }: TaskGroupProps) {
  return (
    <div className="text-content-2">
      <TaskItemTitle>{title}</TaskItemTitle>

      <ul className="text-sm">
        {tasks.map((task) => (
          <TaskCard key={task.taskId} task={task} />
        ))}
      </ul>
    </div>
  );
}
