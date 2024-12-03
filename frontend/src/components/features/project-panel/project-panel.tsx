import { cn } from "#/utils/utils";
import { ProjectCard } from "./project-card";

interface UserProject {
  id: string;
  name: string;
  repo?: string;
  lastUpdated: string;
}

const projects: UserProject[] = [
  {
    id: "1",
    name: "Project 1",
    repo: "org/repo",
    lastUpdated: "2021-10-01T12:00:00Z",
  },
  {
    id: "2",
    name: "Project 2",
    lastUpdated: "2021-10-01T12:00:00Z",
  },
  {
    id: "3",
    name: "Project 3",
    lastUpdated: "2021-10-01T12:00:00Z",
  },
];

export function ProjectPanel() {
  return (
    <div
      className={cn(
        "w-[350px] h-full border border-neutral-700 bg-neutral-900 rounded-xl z-20",
        "absolute left-[calc(100%+12px)]", // 12px padding (sidebar parent)
      )}
    >
      <div className="pt-4 px-4">
        <button
          type="button"
          className="font-bold bg-[#4465DB] px-2 py-1 rounded"
        >
          + New Project
        </button>
      </div>
      {projects.map((project) => (
        <ProjectCard
          key={project.id}
          onClick={() => {}}
          onDelete={() => {}}
          name={project.name}
          repo={project.repo}
          lastUpdated={project.lastUpdated}
        />
      ))}
    </div>
  );
}
