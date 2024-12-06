import React from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router";
import { ProjectCard } from "./project-card";
import { useUserConversations } from "#/hooks/query/use-user-conversations";
import { useDeleteConversation } from "#/hooks/mutation/use-delete-conversation";
import { ConfirmDeleteModal } from "./confirm-delete-modal";
import { NewProjectButton } from "./new-project-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { useUpdateConversation } from "#/hooks/mutation/use-update-conversation";
import { useEndSession } from "#/hooks/use-end-session";
import { ExitProjectModal } from "./exit-project-modal";

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
  const [confirmExitProjectModalVisible, setConfirmExitProjectModalVisible] =
    React.useState(false);
  const [selectedConversationId, setSelectedConversationId] = React.useState<
    string | null
  >(null);

  const { data: conversations, isFetching, error } = useUserConversations();

  const { mutate: deleteConversation } = useDeleteConversation();
  const { mutate: updateConversation } = useUpdateConversation();

  const handleDeleteProject = (conversationId: string) => {
    setConfirmDeleteModalVisible(true);
    setSelectedConversationId(conversationId);
  };

  const handleConfirmDelete = () => {
    if (selectedConversationId) {
      deleteConversation({ conversationId: selectedConversationId });
      setConfirmDeleteModalVisible(false);

      const cid = searchParams.get("cid");
      if (cid === selectedConversationId) {
        endSession();
      }
    }
  };

  const handleChangeTitle = (
    conversationId: string,
    oldTitle: string,
    newTitle: string,
  ) => {
    if (oldTitle !== newTitle)
      updateConversation({ id: conversationId, project: { name: newTitle } });
  };

  const handleClickCard = (conversationId: string) => {
    navigate(`/conversation?cid=${conversationId}`);
    onClose();
  };

  return (
    <div
      data-testid="project-panel"
      className="w-[350px] h-full border border-neutral-700 bg-neutral-800 rounded-xl"
    >
      <div className="pt-4 px-4 flex items-center justify-between">
        {location.pathname.startsWith("/conversation") && (
          <NewProjectButton
            onClick={() => setConfirmExitProjectModalVisible(true)}
          />
        )}
        {isFetching && <LoadingSpinner size="small" />}
      </div>
      {error && (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-danger">{error.message}</p>
        </div>
      )}
      {conversations?.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-neutral-400">No projects found</p>
        </div>
      )}
      {conversations?.map((project) => (
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

      {confirmExitProjectModalVisible && (
        <ExitProjectModal
          onConfirm={() => {
            endSession();
            onClose();
          }}
          onClose={() => setConfirmExitProjectModalVisible(false)}
        />
      )}
    </div>
  );
}
