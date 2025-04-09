import { TaskCard } from "./task-card";
import { TaskItem } from "./task.types";

interface TaskGroupProps {
  title: string;
  tasks: TaskItem[];
}

export function TaskGroup({ title, tasks }: TaskGroupProps) {
  return (
    <div className="text-content-2">
      <div className="py-3 border-b-1 border-[#717888]">
        <h3 className="text-[16px] leading-6 font-[500]">{title}</h3>
      </div>

      <ul className="text-sm">
        {tasks.map((task) => (
          <TaskCard key={task.taskId} task={task} />
        ))}
      </ul>
    </div>
  );
}
