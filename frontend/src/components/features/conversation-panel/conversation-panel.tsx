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
import { setCurrentPathViewed } from "#/state/file-state-slice";
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

  const closeConversationPanel = () => {
    dispatch(setCurrentPathViewed(""));
    onClose();
  };

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
        }
      );
    }
  };

  const handleChangeTitle = (
    conversationId: string,
    oldTitle: string,
    newTitle: string
  ) => {
    if (oldTitle !== newTitle)
      updateConversation({
        id: conversationId,
        conversation: { title: newTitle },
      });
  };

  const handleEndSession = () => {
    dispatch(setCurrentPathViewed(""));
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
      className="absolute left-3 top-[125px] max-h-[calc(100dvh-125px)] min-h-[150px] w-[240px] overflow-y-auto rounded-2xl bg-white px-2 pt-2 dark:bg-[#0F0F0F] max-md:top-[0px]"
    >
      {isFetching && (
        <div className="absolute flex h-full w-full items-center justify-center">
          <LoadingSpinner size="small" />
        </div>
      )}
      {error && (
        <div className="flex h-full flex-col items-center justify-center">
          <p className="text-danger">{error.message}</p>
        </div>
      )}
      {conversations?.length === 0 && (
        <div className="flex h-full min-h-[80px] flex-col items-center justify-center">
          <p className="text-neutral-400">
            {t(I18nKey.CONVERSATION$NO_CONVERSATIONS)}
          </p>
        </div>
      )}

      {groupedConversations && (
        <>
          {groupedConversations.today.length > 0 && (
            <div className="mb-2 flex flex-col gap-[2px]">
              <div className="flex items-center justify-between">
                <h3 className="px-4 text-sm font-medium text-neutral-800 dark:text-neutral-400">
                  Today
                </h3>
                <div
                  onClick={handleEndSession}
                  className="mr-1 cursor-pointer rounded-full p-1 hover:bg-neutral-1000 dark:hover:bg-[#262525]"
                >
                  <PlusIcon width={20} height={20} />
                </div>
              </div>
              {groupedConversations.today.map((project) => (
                <NavLink
                  key={project.conversation_id}
                  to={`/conversations/${project.conversation_id}`}
                  onClick={closeConversationPanel}
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
                          title
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
            <div className="mb-2 flex flex-col gap-[2px]">
              <h3 className="px-4 text-sm font-medium text-neutral-800 dark:text-neutral-400">
                Yesterday
              </h3>
              {groupedConversations.yesterday.map((project) => (
                <NavLink
                  key={project.conversation_id}
                  to={`/conversations/${project.conversation_id}`}
                  onClick={closeConversationPanel}
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
                          title
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
            <div className="mb-2 flex flex-col gap-[2px]">
              <h3 className="px-4 text-sm font-medium text-neutral-800 dark:text-neutral-400">
                This Week
              </h3>
              {groupedConversations.thisWeek.map((project) => (
                <NavLink
                  key={project.conversation_id}
                  to={`/conversations/${project.conversation_id}`}
                  onClick={closeConversationPanel}
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
                          title
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
            <div className="mb-2 flex flex-col gap-[2px]">
              <h3 className="px-4 text-sm font-medium text-neutral-800 dark:text-neutral-400">
                This Month
              </h3>
              {groupedConversations.thisMonth.map((project) => (
                <NavLink
                  key={project.conversation_id}
                  to={`/conversations/${project.conversation_id}`}
                  onClick={closeConversationPanel}
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
                          title
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
            <div className="mb-2 flex flex-col gap-[2px]">
              <h3 className="px-4 text-sm font-medium text-neutral-800 dark:text-neutral-400">
                Older
              </h3>
              {groupedConversations.older.map((project) => (
                <NavLink
                  key={project.conversation_id}
                  to={`/conversations/${project.conversation_id}`}
                  onClick={closeConversationPanel}
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
                          title
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
