import { TaskCard } from "./task-card";
import { TaskItemTitle } from "./task-item-title";
import { SuggestedTask } from "./task.types";

interface TaskGroupProps {
  title: string;
  tasks: SuggestedTask[];
}

export function TaskGroup({ title, tasks }: TaskGroupProps) {
  return (
    <div className="text-content-2">
      <TaskItemTitle>{title}</TaskItemTitle>

      <ul className="text-sm">
        {tasks.map((task) => (
          <TaskCard key={task.issue_number} task={task} />
        ))}
      </ul>
    </div>
  );
}
