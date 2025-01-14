import React from "react";
import { NavLink, useParams } from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { ConversationCard } from "./conversation-card";
import { useUserConversations } from "#/hooks/query/use-user-conversations";
import { useDeleteConversation } from "#/hooks/mutation/use-delete-conversation";
import { ConfirmDeleteModal } from "./confirm-delete-modal";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { useUpdateConversation } from "#/hooks/mutation/use-update-conversation";
import { useEndSession } from "#/hooks/use-end-session";
import { ExitConversationModal } from "./exit-conversation-modal";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";

interface ConversationPanelProps {
  onClose: () => void;
}

export function ConversationPanel({ onClose }: ConversationPanelProps) {
  const { t } = useTranslation();
  const { conversationId: cid } = useParams();
  const endSession = useEndSession();
  const ref = useClickOutsideElement<HTMLDivElement>(onClose);

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
        conversation: { title: newTitle },
      });
  };

  return (
    <div
      ref={ref}
      data-testid="conversation-panel"
      className="w-[350px] h-full border border-neutral-700 bg-neutral-800 rounded-xl overflow-y-auto"
    >
      <div className="pt-4 px-4 flex items-center justify-between">
        {isFetching && <LoadingSpinner size="small" />}
      </div>
      {error && (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-danger">{error.message}</p>
        </div>
      )}
      {conversations?.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-neutral-400">
            {t(I18nKey.CONVERSATION$NO_CONVERSATIONS)}
          </p>
        </div>
      )}
      {conversations?.map((project) => (
        <NavLink
          key={project.conversation_id}
          to={`/conversations/${project.conversation_id}`}
          onClick={onClose}
        >
          {({ isActive }) => (
            <ConversationCard
              isActive={isActive}
              onDelete={() => handleDeleteProject(project.conversation_id)}
              onChangeTitle={(title) =>
                handleChangeTitle(project.conversation_id, project.title, title)
              }
              title={project.title}
              selectedRepository={project.selected_repository}
              lastUpdatedAt={project.last_updated_at}
              status={project.status}
            />
          )}
        </NavLink>
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
