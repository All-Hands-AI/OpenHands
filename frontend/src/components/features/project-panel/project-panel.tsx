import React from "react";
import { useMutation } from "@tanstack/react-query";
import { cn } from "#/utils/utils";
import { ProjectCard } from "./project-card";
import { useUserProjects } from "#/hooks/query/use-user-projects";
import { useDeleteProject } from "#/hooks/mutation/use-delete-project";
import { ConfirmDeleteModal } from "./confirm-delete-modal";
import { NewProjectButton } from "./new-project-button";
import { UserProject } from "#/api/open-hands.types";
import OpenHands from "#/api/open-hands";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import RefreshIcon from "#/icons/refresh.svg?react";

export function ProjectPanel() {
  const [confirmDeleteModalVisible, setConfirmDeleteModalVisible] =
    React.useState(false);
  const [selectedProjectId, setSelectedProjectId] = React.useState<
    string | null
  >(null);

  const {
    data: projects,
    isFetching,
    refetch: refetchUserProjects,
    error,
  } = useUserProjects();
  const { mutate: deleteProject } = useDeleteProject();

  const { mutate: updateProject } = useMutation({
    mutationFn: (variables: {
      id: string;
      project: Partial<Omit<UserProject, "id">>;
    }) => OpenHands.updateUserProject(variables.id, variables.project),
  });

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
      <div className="pt-4 px-4 flex items-center justify-between">
        <NewProjectButton />
        {!isFetching && (
          <button
            type="button"
            data-testid="refresh-button"
            onClick={() => refetchUserProjects()}
          >
            <RefreshIcon width={24} height={24} />
          </button>
        )}
        {isFetching && <LoadingSpinner size="small" />}
      </div>
      {error && (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-danger">{error.message}</p>
        </div>
      )}
      {projects?.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-neutral-400">No projects found</p>
        </div>
      )}
      {projects?.map((project) => (
        <ProjectCard
          key={project.id}
          onClick={() => {}}
          onDelete={() => handleDeleteProject(project.id)}
          onChangeTitle={(title) =>
            updateProject({ id: project.id, project: { name: title } })
          }
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
