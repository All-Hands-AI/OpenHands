import React from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router";
import { ProjectCard } from "./project-card";
import { useUserProjects } from "#/hooks/query/use-user-projects";
import { useDeleteProject } from "#/hooks/mutation/use-delete-project";
import { ConfirmDeleteModal } from "./confirm-delete-modal";
import { NewProjectButton } from "./new-project-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { useUpdateProject } from "#/hooks/mutation/use-update-project";
import { useEndSession } from "#/hooks/use-end-session";

interface ProjectPanelProps {
  onClose: () => void;
}

export function ProjectPanel({ onClose }: ProjectPanelProps) {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();

  const endSession = useEndSession();

  const [confirmDeleteModalVisible, setConfirmDeleteModalVisible] =
    React.useState(false);
  const [selectedProjectId, setSelectedProjectId] = React.useState<
    string | null
  >(null);

  const { data: projects, isFetching, error } = useUserProjects();

  const { mutate: deleteProject } = useDeleteProject();
  const { mutate: updateProject } = useUpdateProject();

  const handleDeleteProject = (projectId: string) => {
    setConfirmDeleteModalVisible(true);
    setSelectedProjectId(projectId);
  };

  const handleConfirmDelete = () => {
    if (selectedProjectId) {
      deleteProject({ projectId: selectedProjectId });
      setConfirmDeleteModalVisible(false);

      const cid = searchParams.get("cid");
      if (cid === selectedProjectId) {
        endSession();
      }
    }
  };

  const handleChangeTitle = (
    projectId: string,
    oldTitle: string,
    newTitle: string,
  ) => {
    if (oldTitle !== newTitle)
      updateProject({ id: projectId, project: { name: newTitle } });
  };

  const handleClickCard = (projectId: string) => {
    navigate(`/conversation?cid=${projectId}`);
    onClose();
  };

  return (
    <div
      data-testid="project-panel"
      className="w-[350px] h-full border border-neutral-700 bg-neutral-800 rounded-xl"
    >
      <div className="pt-4 px-4 flex items-center justify-between">
        {location.pathname.startsWith("/conversation") && <NewProjectButton />}
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
          onClick={() => handleClickCard(project.id)}
          onDelete={() => handleDeleteProject(project.id)}
          onChangeTitle={(title) =>
            handleChangeTitle(project.id, project.name, title)
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
