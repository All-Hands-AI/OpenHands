import React from "react";
import { useLocation, useNavigate, useParams } from "react-router";
import { ConversationCard } from "./conversation-card";
import { useUserConversations } from "#/hooks/query/use-user-conversations";
import { useDeleteConversation } from "#/hooks/mutation/use-delete-conversation";
import { ConfirmDeleteModal } from "./confirm-delete-modal";
import { NewConversationButton } from "./new-conversation-button";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { useUpdateConversation } from "#/hooks/mutation/use-update-conversation";
import { useEndSession } from "#/hooks/use-end-session";
import { ExitConversationModal } from "./exit-conversation-modal";

interface ConversationPanelProps {
  onClose: () => void;
}

export function ConversationPanel({ onClose }: ConversationPanelProps) {
  const { conversationId: cid } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const endSession = useEndSession();

  const [confirmDeleteModalVisible, setConfirmDeleteModalVisible] =
    React.useState(false);
  const [
    confirmExitConversationModalVisible,
    setConfirmExitConversationModalVisible,
  ] = React.useState(false);
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
      updateConversation({
        id: conversationId,
        conversation: { name: newTitle },
      });
  };

  const handleClickCard = (conversationId: string) => {
    navigate(`/conversations/${conversationId}`);
    onClose();
  };

  return (
    <div
      data-testid="conversation-panel"
      className="w-[350px] h-full border border-neutral-700 bg-neutral-800 rounded-xl"
    >
      <div className="pt-4 px-4 flex items-center justify-between">
        {location.pathname.startsWith("/conversation") && (
          <NewConversationButton
            onClick={() => setConfirmExitConversationModalVisible(true)}
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
          <p className="text-neutral-400">No conversations found</p>
        </div>
      )}
      {conversations?.map((project) => (
        <ConversationCard
          key={project.conversation_id}
          onClick={() => handleClickCard(project.conversation_id)}
          onDelete={() => handleDeleteProject(project.conversation_id)}
          onChangeTitle={(title) =>
            handleChangeTitle(project.conversation_id, project.name, title)
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

      {confirmExitConversationModalVisible && (
        <ExitConversationModal
          onConfirm={() => {
            endSession();
            onClose();
          }}
          onClose={() => setConfirmExitConversationModalVisible(false)}
        />
      )}
    </div>
  );
}
