import { useTranslation } from "react-i18next";
import React from "react";
import posthog from "posthog-js";
import { useParams, useNavigate } from "react-router";
import { useSelector } from "react-redux";
import { useWsClient } from "#/context/ws-client-provider";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";
import { RootState } from "#/store";
import { isSystemMessage } from "#/types/core/guards";
import { ConversationStatus } from "#/types/conversation-status";
import OpenHands from "#/api/open-hands";
import { useDeleteConversation } from "./mutation/use-delete-conversation";
import { useStopConversation } from "./mutation/use-stop-conversation";
import { useGetTrajectory } from "./mutation/use-get-trajectory";
import { downloadTrajectory } from "#/utils/download-trajectory";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { I18nKey } from "#/i18n/declaration";

interface UseConversationNameContextMenuProps {
  conversationId?: string;
  conversationStatus?: ConversationStatus;
  showOptions?: boolean;
  onContextMenuToggle?: (isOpen: boolean) => void;
}

export function useConversationNameContextMenu({
  conversationId,
  conversationStatus = "STOPPED",
  showOptions = false,
  onContextMenuToggle,
}: UseConversationNameContextMenuProps) {
  const { t } = useTranslation();
  const { conversationId: currentConversationId } = useParams();
  const navigate = useNavigate();
  const { parsedEvents } = useWsClient();
  const { mutate: deleteConversation } = useDeleteConversation();
  const { mutate: stopConversation } = useStopConversation();
  const { mutate: getTrajectory } = useGetTrajectory();
  const metrics = useSelector((state: RootState) => state.metrics);

  const [metricsModalVisible, setMetricsModalVisible] = React.useState(false);
  const [systemModalVisible, setSystemModalVisible] = React.useState(false);
  const [microagentsModalVisible, setMicroagentsModalVisible] =
    React.useState(false);
  const [confirmDeleteModalVisible, setConfirmDeleteModalVisible] =
    React.useState(false);
  const [confirmStopModalVisible, setConfirmStopModalVisible] =
    React.useState(false);

  const systemMessage = parsedEvents.find(isSystemMessage);

  const handleDelete = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setConfirmDeleteModalVisible(true);
    onContextMenuToggle?.(false);
  };

  const handleStop = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setConfirmStopModalVisible(true);
    onContextMenuToggle?.(false);
  };

  const handleConfirmDelete = () => {
    if (conversationId) {
      deleteConversation(
        { conversationId },
        {
          onSuccess: () => {
            if (conversationId === currentConversationId) {
              navigate("/");
            }
          },
        },
      );
    }
    setConfirmDeleteModalVisible(false);
  };

  const handleConfirmStop = () => {
    if (conversationId) {
      stopConversation(
        { conversationId },
        {
          onSuccess: () => {
            if (conversationId === currentConversationId) {
              navigate("/");
            }
          },
        },
      );
    }
    setConfirmStopModalVisible(false);
  };

  const handleEdit = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    event.stopPropagation();
    // This will be handled by the parent component to switch to edit mode
    onContextMenuToggle?.(false);
  };

  const handleExportConversation = (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    event.preventDefault();
    event.stopPropagation();

    if (!conversationId) {
      displayErrorToast(t(I18nKey.CONVERSATION$DOWNLOAD_ERROR));
      return;
    }

    getTrajectory(conversationId, {
      onSuccess: async (data) => {
        await downloadTrajectory(
          conversationId ?? t(I18nKey.CONVERSATION$UNKNOWN),
          data.trajectory,
        );
      },
      onError: () => {
        displayErrorToast(t(I18nKey.CONVERSATION$DOWNLOAD_ERROR));
      },
    });

    onContextMenuToggle?.(false);
  };

  const handleDownloadViaVSCode = async (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    event.preventDefault();
    event.stopPropagation();
    posthog.capture("download_via_vscode_button_clicked");

    // Fetch the VS Code URL from the API
    if (conversationId) {
      try {
        const data = await OpenHands.getVSCodeUrl(conversationId);
        if (data.vscode_url) {
          const transformedUrl = transformVSCodeUrl(data.vscode_url);
          if (transformedUrl) {
            window.open(transformedUrl, "_blank");
          }
        }
        // VS Code URL not available
      } catch (error) {
        // Failed to fetch VS Code URL
      }
    }

    onContextMenuToggle?.(false);
  };

  const handleDisplayCost = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setMetricsModalVisible(true);
    onContextMenuToggle?.(false);
  };

  const handleShowAgentTools = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    setSystemModalVisible(true);
    onContextMenuToggle?.(false);
  };

  const handleShowMicroagents = (
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    event.stopPropagation();
    setMicroagentsModalVisible(true);
    onContextMenuToggle?.(false);
  };

  return {
    // Handlers
    handleDelete,
    handleStop,
    handleEdit,
    handleExportConversation,
    handleDownloadViaVSCode,
    handleDisplayCost,
    handleShowAgentTools,
    handleShowMicroagents,
    handleConfirmDelete,
    handleConfirmStop,

    // Modal states
    metricsModalVisible,
    setMetricsModalVisible,
    systemModalVisible,
    setSystemModalVisible,
    microagentsModalVisible,
    setMicroagentsModalVisible,
    confirmDeleteModalVisible,
    setConfirmDeleteModalVisible,
    confirmStopModalVisible,
    setConfirmStopModalVisible,

    // Data
    metrics,
    systemMessage,

    // Computed values for conditional rendering
    shouldShowStop: conversationStatus !== "STOPPED",
    shouldShowDownload: Boolean(conversationId && showOptions),
    shouldShowExport: Boolean(conversationId && showOptions),
    shouldShowDisplayCost: showOptions,
    shouldShowAgentTools: Boolean(showOptions && systemMessage),
    shouldShowMicroagents: Boolean(showOptions && conversationId),
  };
}
