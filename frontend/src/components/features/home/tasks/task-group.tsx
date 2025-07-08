import { TaskCard } from "./task-card";
import { TaskItemTitle } from "./task-item-title";
import { SuggestedTask } from "./task.types";

interface TaskGroupProps {
  title: string;
  tasks: SuggestedTask[];
  isLastTaskGroup?: boolean;
}

export function TaskGroup({ title, tasks, isLastTaskGroup }: TaskGroupProps) {
  const numberOfTasks = tasks.length;

  return (
    <div className="text-content-2">
      <TaskItemTitle>{title}</TaskItemTitle>

      <ul className="text-sm">
        {tasks.map((task, index) => {
          const isLastTask = index === numberOfTasks - 1;
          return (
            <TaskCard
              key={task.issue_number}
              task={task}
              isLastTask={isLastTaskGroup && isLastTask}
            />
          );
        })}
      </ul>
    </div>
  );
}
