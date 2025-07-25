import { FaBitbucket, FaGithub, FaGitlab } from "react-icons/fa6";
import { TaskCard } from "./task-card";
import { TaskItemTitle } from "./task-item-title";
import { SuggestedTask } from "./task.types";

interface TaskGroupProps {
  title: string;
  tasks: SuggestedTask[];
}

export function TaskGroup({ title, tasks }: TaskGroupProps) {
  const gitProvider = tasks.length > 0 ? tasks[0].git_provider : null;

  return (
    <div className="text-content-2">
      <div className="flex items-center gap-2 border-b-1 border-[#717888]">
        {gitProvider === "github" && <FaGithub size={14} />}
        {gitProvider === "gitlab" && <FaGitlab />}
        {gitProvider === "bitbucket" && <FaBitbucket />}
        <TaskItemTitle>{title}</TaskItemTitle>
      </div>

      <ul className="text-sm">
        {tasks.map((task) => (
          <TaskCard key={task.issue_number} task={task} />
        ))}
      </ul>
    </div>
  );
}
