import React from "react";
import { NavLink, useParams, useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { I18nKey } from "#/i18n/declaration";
import { ConversationCard } from "./conversation-card";
import { usePaginatedConversations } from "#/hooks/query/use-paginated-conversations";
import { useInfiniteScroll } from "#/hooks/use-infinite-scroll";
import { useDeleteConversation } from "#/hooks/mutation/use-delete-conversation";
import { useStopConversation } from "#/hooks/mutation/use-stop-conversation";
import { ConfirmDeleteModal } from "./confirm-delete-modal";
import { ConfirmStopModal } from "./confirm-stop-modal";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { ExitConversationModal } from "./exit-conversation-modal";
import { useClickOutsideElement } from "#/hooks/use-click-outside-element";
import { Provider } from "#/types/settings";
import { useUpdateConversation } from "#/hooks/mutation/use-update-conversation";
import { displaySuccessToast } from "#/utils/custom-toast-handlers";
import { useWsClient } from "#/context/ws-client-provider";

interface ConversationPanelProps {
  onClose: () => void;
}

export function ConversationPanel({ onClose }: ConversationPanelProps) {
  const { t } = useTranslation();
  const { conversationId: currentConversationId } = useParams();
  const ref = useClickOutsideElement<HTMLDivElement>(onClose);
  const navigate = useNavigate();

  const [confirmDeleteModalVisible, setConfirmDeleteModalVisible] =
    React.useState(false);
  const [confirmStopModalVisible, setConfirmStopModalVisible] =
    React.useState(false);
  const [
    confirmExitConversationModalVisible,
    setConfirmExitConversationModalVisible,
  ] = React.useState(false);
  const [selectedConversationId, setSelectedConversationId] = React.useState<
    string | null
  >(null);
  const [openContextMenuId, setOpenContextMenuId] = React.useState<
    string | null
  >(null);

  const {
    data,
    isFetching,
    error,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = usePaginatedConversations();

  // Flatten all pages into a single array of conversations
  const conversations = data?.pages.flatMap((page) => page.results) ?? [];

  const { mutate: deleteConversation } = useDeleteConversation();
  const { mutate: stopConversation } = useStopConversation();
  const { mutate: updateConversation } = useUpdateConversation();

  // WebSocket client and query client for real-time updates
  const { events } = useWsClient();
  const queryClient = useQueryClient();

  // Listen for title updates via WebSocket
  React.useEffect(() => {
    if (!events.length) {
      return;
    }
    const event = events[events.length - 1];

    // Check if this is a status update with a conversation title
    if (
      typeof event === "object" &&
      event !== null &&
      "status_update" in event &&
      event.status_update === true &&
      "conversation_title" in event &&
      typeof event.conversation_title === "string"
    ) {
      // Invalidate the conversations query to refetch with updated titles
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    }
  }, [events.length, queryClient]);

  // Set up infinite scroll
  const scrollContainerRef = useInfiniteScroll({
    hasNextPage: !!hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
    threshold: 200, // Load more when 200px from bottom
  });

  const handleDeleteProject = (conversationId: string) => {
    setConfirmDeleteModalVisible(true);
    setSelectedConversationId(conversationId);
  };

  const handleStopConversation = (conversationId: string) => {
    setConfirmStopModalVisible(true);
    setSelectedConversationId(conversationId);
  };

  const handleConversationTitleChange = async (
    conversationId: string,
    newTitle: string,
  ) => {
    updateConversation(
      { conversationId, newTitle },
      {
        onSuccess: () => {
          displaySuccessToast(t(I18nKey.CONVERSATION$TITLE_UPDATED));
        },
      },
    );
  };

  const handleConfirmDelete = () => {
    if (selectedConversationId) {
      deleteConversation(
        { conversationId: selectedConversationId },
        {
          onSuccess: () => {
            if (selectedConversationId === currentConversationId) {
              navigate("/");
            }
          },
        },
      );
    }
  };

  const handleConfirmStop = () => {
    if (selectedConversationId) {
      stopConversation(
        { conversationId: selectedConversationId },
        {
          onSuccess: () => {
            if (selectedConversationId === currentConversationId) {
              navigate("/");
            }
          },
        },
      );
    }
  };

  return (
    <div
      ref={(node) => {
        // TODO: Combine both refs somehow
        if (ref.current !== node) ref.current = node;
        if (scrollContainerRef.current !== node)
          scrollContainerRef.current = node;
      }}
      data-testid="conversation-panel"
      className="w-[350px] h-full border border-neutral-700 bg-base-secondary rounded-xl overflow-y-auto absolute"
    >
      {isFetching && conversations.length === 0 && (
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
              onStop={() => handleStopConversation(project.conversation_id)}
              onChangeTitle={(title) =>
                handleConversationTitleChange(project.conversation_id, title)
              }
              title={project.title}
              selectedRepository={{
                selected_repository: project.selected_repository,
                selected_branch: project.selected_branch,
                git_provider: project.git_provider as Provider,
              }}
              lastUpdatedAt={project.last_updated_at}
              createdAt={project.created_at}
              conversationStatus={project.status}
              conversationId={project.conversation_id}
              contextMenuOpen={openContextMenuId === project.conversation_id}
              onContextMenuToggle={(isOpen) =>
                setOpenContextMenuId(isOpen ? project.conversation_id : null)
              }
            />
          )}
        </NavLink>
      ))}

      {/* Loading indicator for fetching more conversations */}
      {isFetchingNextPage && (
        <div className="flex justify-center py-4">
          <LoadingSpinner size="small" />
        </div>
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

      {confirmStopModalVisible && (
        <ConfirmStopModal
          onConfirm={() => {
            handleConfirmStop();
            setConfirmStopModalVisible(false);
          }}
          onCancel={() => setConfirmStopModalVisible(false)}
        />
      )}

      {confirmExitConversationModalVisible && (
        <ExitConversationModal
          onConfirm={() => {
            onClose();
          }}
          onClose={() => setConfirmExitConversationModalVisible(false)}
        />
      )}
    </div>
  );
}
