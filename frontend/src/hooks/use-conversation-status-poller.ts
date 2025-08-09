import React from "react";
import { useQuery } from "@tanstack/react-query";
import OpenHands from "#/api/open-hands";
import { ConversationStatus } from "#/types/conversation-status";

interface UseConversationStatusPollerOptions {
  conversationId: string | null;
  enabled?: boolean;
  onStatusChange?: (status: ConversationStatus, conversationId: string) => void;
  onReady?: (conversationId: string) => void;
  onStopped?: (conversationId: string) => void;
}

/**
 * Hook to poll conversation status until it's ready for WebSocket connection
 */
export const useConversationStatusPoller = ({
  conversationId,
  enabled = true,
  onStatusChange,
  onReady,
  onStopped,
}: UseConversationStatusPollerOptions) => {
  const query = useQuery({
    queryKey: ["conversation-status-poll", conversationId],
    queryFn: async () => {
      if (!conversationId) return null;
      return OpenHands.getConversation(conversationId);
    },
    enabled: enabled && !!conversationId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "STARTING") {
        return 3000; // Poll every 3 seconds while starting
      }
      return false; // Stop polling once not starting
    },
    retry: false,
  });

  // Handle status changes
  React.useEffect(() => {
    if (!query.data || !conversationId) return;

    const status = query.data.status;
    
    // Call status change callback
    if (onStatusChange) {
      onStatusChange(status, conversationId);
    }

    // Handle specific status transitions
    if (status === "RUNNING" && onReady) {
      onReady(conversationId);
    } else if (status === "STOPPED" && onStopped) {
      onStopped(conversationId);
    }
  }, [query.data?.status, conversationId, onStatusChange, onReady, onStopped]);

  return {
    conversation: query.data,
    status: query.data?.status,
    isPolling: query.isFetching && query.data?.status === "STARTING",
    isReady: query.data?.status === "RUNNING",
    isStopped: query.data?.status === "STOPPED",
    error: query.error,
  };
};