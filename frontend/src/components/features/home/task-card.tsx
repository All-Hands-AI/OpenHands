import { TaskItem } from "./task.types";

interface TaskCardProps {
  task: TaskItem;
}

export function TaskCard({ task }: TaskCardProps) {
  return (
    <li className="py-3 border-b-1 border-[#717888] flex items-center pr-6">
      <span>{task.taskId}</span>

      <div className="w-full pl-8">
        <p className="font-semibold">{task.title}</p>
        <p>{task.description}</p>
      </div>

      <a
        href="http://"
        target="_blank"
        rel="noopener noreferrer"
        className="underline underline-offset-2"
      >
        Launch
      </a>
    </li>
  );
}
