import React from "react";
import { NavLink, useParams } from "react-router";
import PlusIcon from "#/icons/plus.svg?react";
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
import { groupConversationsByDate } from "#/utils/group-conversations-by-date";
import { setCurrentAgentState } from "#/state/agent-slice";
import { AgentState } from "#/types/agent-state";
import { useDispatch } from "react-redux";

interface ConversationPanelProps {
  onClose: () => void;
}

export function ConversationPanel({ onClose }: ConversationPanelProps) {
  const { t } = useTranslation();
  const { conversationId: cid } = useParams();
  const endSession = useEndSession();
  const ref = useClickOutsideElement<HTMLDivElement>(onClose);
  const dispatch = useDispatch();
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
      deleteConversation(
        { conversationId: selectedConversationId },
        {
          onSuccess: () => {
            if (cid === selectedConversationId) {
              endSession();
            }
          },
        },
      );
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

  const handleEndSession = () => {
    dispatch(setCurrentAgentState(AgentState.LOADING));
    endSession();
    onClose();
  };

  const groupedConversations = React.useMemo(() => {
    if (!conversations) return null;
    return groupConversationsByDate(conversations);
  }, [conversations]);

  return (
    <div
      ref={ref}
      data-testid="conversation-panel"
      className="w-[240px] pt-2 px-2 min-h-[150px] max-h-[calc(100dvh-125px)] bg-[#0F0F0F] rounded-2xl overflow-y-auto top-[125px] left-3 max-md:top-[0px] absolute"
    >
      {isFetching && (
        <div className="w-full h-full absolute flex justify-center items-center">
          <LoadingSpinner size="small" />
        </div>
      )}
      {error && (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-danger">{error.message}</p>
        </div>
      )}
      {conversations?.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full min-h-[80px]">
          <p className="text-neutral-400">
            {t(I18nKey.CONVERSATION$NO_CONVERSATIONS)}
          </p>
        </div>
      )}

      {groupedConversations && (
        <>
          {groupedConversations.today.length > 0 && (
            <div className="mb-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-neutral-400 px-4 py-2">
                  Today
                </h3>
                <div
                  onClick={handleEndSession}
                  className="cursor-pointer mr-1 hover:bg-[#262525] rounded-full p-1"
                >
                  <PlusIcon width={20} height={20} />
                </div>
              </div>
              {groupedConversations.today.map((project) => (
                <NavLink
                  key={project.conversation_id}
                  to={`/conversations/${project.conversation_id}`}
                  onClick={onClose}
                  className="my-1 block"
                >
                  {({ isActive }) => (
                    <ConversationCard
                      isActive={isActive}
                      onDelete={() =>
                        handleDeleteProject(project.conversation_id)
                      }
                      onChangeTitle={(title) =>
                        handleChangeTitle(
                          project.conversation_id,
                          project.title,
                          title,
                        )
                      }
                      title={project.title}
                      selectedRepository={project.selected_repository}
                      lastUpdatedAt={project.last_updated_at}
                      createdAt={project.created_at}
                      status={project.status}
                      conversationId={project.conversation_id}
                    />
                  )}
                </NavLink>
              ))}
            </div>
          )}

          {groupedConversations.yesterday.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-neutral-400 px-4 py-2">
                Yesterday
              </h3>
              {groupedConversations.yesterday.map((project) => (
                <NavLink
                  key={project.conversation_id}
                  to={`/conversations/${project.conversation_id}`}
                  onClick={onClose}
                >
                  {({ isActive }) => (
                    <ConversationCard
                      isActive={isActive}
                      onDelete={() =>
                        handleDeleteProject(project.conversation_id)
                      }
                      onChangeTitle={(title) =>
                        handleChangeTitle(
                          project.conversation_id,
                          project.title,
                          title,
                        )
                      }
                      title={project.title}
                      selectedRepository={project.selected_repository}
                      lastUpdatedAt={project.last_updated_at}
                      createdAt={project.created_at}
                      status={project.status}
                      conversationId={project.conversation_id}
                    />
                  )}
                </NavLink>
              ))}
            </div>
          )}

          {groupedConversations.thisWeek.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-neutral-400 px-4 py-2">
                This Week
              </h3>
              {groupedConversations.thisWeek.map((project) => (
                <NavLink
                  key={project.conversation_id}
                  to={`/conversations/${project.conversation_id}`}
                  onClick={onClose}
                >
                  {({ isActive }) => (
                    <ConversationCard
                      isActive={isActive}
                      onDelete={() =>
                        handleDeleteProject(project.conversation_id)
                      }
                      onChangeTitle={(title) =>
                        handleChangeTitle(
                          project.conversation_id,
                          project.title,
                          title,
                        )
                      }
                      title={project.title}
                      selectedRepository={project.selected_repository}
                      lastUpdatedAt={project.last_updated_at}
                      createdAt={project.created_at}
                      status={project.status}
                      conversationId={project.conversation_id}
                    />
                  )}
                </NavLink>
              ))}
            </div>
          )}

          {groupedConversations.thisMonth.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-neutral-400 px-4 py-2">
                This Month
              </h3>
              {groupedConversations.thisMonth.map((project) => (
                <NavLink
                  key={project.conversation_id}
                  to={`/conversations/${project.conversation_id}`}
                  onClick={onClose}
                >
                  {({ isActive }) => (
                    <ConversationCard
                      isActive={isActive}
                      onDelete={() =>
                        handleDeleteProject(project.conversation_id)
                      }
                      onChangeTitle={(title) =>
                        handleChangeTitle(
                          project.conversation_id,
                          project.title,
                          title,
                        )
                      }
                      title={project.title}
                      selectedRepository={project.selected_repository}
                      lastUpdatedAt={project.last_updated_at}
                      createdAt={project.created_at}
                      status={project.status}
                      conversationId={project.conversation_id}
                    />
                  )}
                </NavLink>
              ))}
            </div>
          )}

          {groupedConversations.older.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-neutral-400 px-4 py-2">
                Older
              </h3>
              {groupedConversations.older.map((project) => (
                <NavLink
                  key={project.conversation_id}
                  to={`/conversations/${project.conversation_id}`}
                  onClick={onClose}
                >
                  {({ isActive }) => (
                    <ConversationCard
                      isActive={isActive}
                      onDelete={() =>
                        handleDeleteProject(project.conversation_id)
                      }
                      onChangeTitle={(title) =>
                        handleChangeTitle(
                          project.conversation_id,
                          project.title,
                          title,
                        )
                      }
                      title={project.title}
                      selectedRepository={project.selected_repository}
                      lastUpdatedAt={project.last_updated_at}
                      createdAt={project.created_at}
                      status={project.status}
                      conversationId={project.conversation_id}
                    />
                  )}
                </NavLink>
              ))}
            </div>
          )}
        </>
      )}

      {confirmDeleteModalVisible && (
        <ConfirmDeleteModal
          onConfirm={() => {
            handleConfirmDelete();
            setConfirmDeleteModalVisible(false);
          }}
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
