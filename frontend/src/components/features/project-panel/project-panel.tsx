import React from "react";
import { cn } from "#/utils/utils";
import { ProjectCard } from "./project-card";
import { useUserProjects } from "#/hooks/query/use-user-projects";
import { useDeleteProject } from "#/hooks/mutation/use-delete-project";
import { ConfirmDeleteModal } from "./confirm-delete-modal";
import { NewProjectButton } from "./new-project-button";

export function ProjectPanel() {
  const [confirmDeleteModalVisible, setConfirmDeleteModalVisible] =
    React.useState(false);
  const [selectedProjectId, setSelectedProjectId] = React.useState<
    string | null
  >(null);

  const { data: projects } = useUserProjects();
  const { mutate: deleteProject } = useDeleteProject();

  const handleDeleteProject = (projectId: string) => {
    setConfirmDeleteModalVisible(true);
    setSelectedProjectId(projectId);
  };

  const handleConfirmDelete = () => {
    if (selectedProjectId) {
      deleteProject({ projectId: selectedProjectId });
      setConfirmDeleteModalVisible(false);
    }
  };

  return (
    <div
      className={cn(
        "w-[350px] h-full border border-neutral-700 bg-neutral-900 rounded-xl z-20",
        "absolute left-[calc(100%+12px)]", // 12px padding (sidebar parent)
      )}
    >
      <div className="pt-4 px-4">
        <NewProjectButton />
      </div>
      {projects?.map((project) => (
        <ProjectCard
          key={project.id}
          onClick={() => {}}
          onDelete={() => handleDeleteProject(project.id)}
          onChangeTitle={() => {}}
          name={project.name}
          repo={project.repo}
          lastUpdated={project.lastUpdated}
          state={project.state}
        />
      ))}

      {confirmDeleteModalVisible && (
        <ConfirmDeleteModal
          onConfirm={handleConfirmDelete}
          onCancel={() => setConfirmDeleteModalVisible(false)}
        />
      )}
    </div>
  );
}
