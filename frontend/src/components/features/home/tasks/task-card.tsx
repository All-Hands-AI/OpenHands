import { SuggestedTask } from "./task.types";

interface TaskCardProps {
  task: SuggestedTask;
}

export function TaskCard({ task }: TaskCardProps) {
  return (
    <li className="py-3 border-b-1 border-[#717888] flex items-center pr-6">
      <span>{task.id}</span>

      <div className="w-full pl-8">
        <p className="font-semibold">{task.type}</p>
        <p>{task.title}</p>
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
