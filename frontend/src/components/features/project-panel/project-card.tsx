import { formatTimeDelta } from "#/utils/format-time-delta";
import { DeleteButton } from "./delete-button";
import { ProjectRepoLink } from "./project-repo-link";
import { ProjectState, ProjectStateIndicator } from "./project-state-indicator";

interface ProjectCardProps {
  onClick: () => void;
  onDelete: () => void;
  name: string;
  repo?: string;
  lastUpdated: string; // ISO 8601
  state?: ProjectState;
}

export function ProjectCard({
  onClick,
  onDelete,
  name,
  repo,
  lastUpdated,
  state = "cold",
}: ProjectCardProps) {
  return (
    <div
      data-testid="project-card"
      onClick={onClick}
      className="h-[100px] w-full px-[18px] py-4 border-b border-neutral-600"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm leading-6 font-semibold">{name}</h3>
        <div className="flex items-center gap-2">
          <ProjectStateIndicator state={state} />
          <DeleteButton onClick={onDelete} />
        </div>
      </div>
      {repo && (
        <ProjectRepoLink repo={repo} onClick={(e) => e.stopPropagation()} />
      )}
      <p className="text-xs text-neutral-400">
        <time>{formatTimeDelta(new Date(lastUpdated))} ago</time>
      </p>
    </div>
  );
}
