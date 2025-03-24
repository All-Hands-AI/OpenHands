import { useDispatch, useSelector } from "react-redux";
import type { Message } from "#/message";
import { RootState } from "#/store";
import {
  addUserMessage,
  addAssistantMessage,
  addAssistantAction,
  addAssistantObservation,
  addErrorMessage,
  clearMessages,
} from "#/state/chat-slice";

/**
 * Hook to access and manipulate chat messages using Redux
 * This is a temporary solution until we fix the double message issue with React Query
 */
export function useChat() {
  console.log("[DOUBLE_MSG_DEBUG] useChat hook initializing (using Redux)", {
    timestamp: new Date().toISOString()
  });
  
  // Use Redux for chat messages
  const dispatch = useDispatch();
  const messages = useSelector((state: RootState) => state.chat.messages);
  
  // Log the messages from Redux
  console.log("[DOUBLE_MSG_DEBUG] useChat using Redux messages:", {
    count: messages.length,
    timestamp: new Date().toISOString()
  });
  
  // Return the Redux actions and messages
  return {
    messages,
    isLoading: false,
    addUserMessage: (payload: {
      content: string;
      imageUrls: string[];
      timestamp: string;
      pending?: boolean;
    }) => {
      console.log("[DOUBLE_MSG_DEBUG] useChat.addUserMessage called (Redux):", {
        messageId: `user-${payload.timestamp}`,
        content: payload.content.substring(0, 30) + (payload.content.length > 30 ? "..." : ""),
        timestamp: new Date().toISOString()
      });
      dispatch(addUserMessage(payload));
    },
    addAssistantMessage: (content: string) => {
      console.log("[DOUBLE_MSG_DEBUG] useChat.addAssistantMessage called (Redux):", {
        content: content.substring(0, 30) + (content.length > 30 ? "..." : ""),
        timestamp: new Date().toISOString()
      });
      dispatch(addAssistantMessage(content));
    },
    addAssistantAction: (action: {
      id: string;
      action: string;
      args: Record<string, unknown>;
    }) => {
      console.log("[DOUBLE_MSG_DEBUG] useChat.addAssistantAction called (Redux):", {
        id: action.id,
        action: action.action,
        timestamp: new Date().toISOString()
      });
      // Convert string id to number for Redux
      const actionWithNumberId = {
        ...action,
        id: Number(action.id),
      };
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      dispatch(addAssistantAction(actionWithNumberId as any));
    },
    addAssistantObservation: (observation: {
      id: string;
      observation: string;
      cause: string;
      content?: string;
      extras?: Record<string, unknown>;
    }) => {
      console.log("[DOUBLE_MSG_DEBUG] useChat.addAssistantObservation called (Redux):", {
        id: observation.id,
        observation: observation.observation,
        cause: observation.cause,
        timestamp: new Date().toISOString()
      });
      // Convert string ids to numbers for Redux
      const observationWithNumberIds = {
        ...observation,
        id: Number(observation.id),
        cause: Number(observation.cause),
      };
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      dispatch(addAssistantObservation(observationWithNumberIds as any));
    },
    addErrorMessage: (payload: { id?: string; message: string }) => {
      console.log("[DOUBLE_MSG_DEBUG] useChat.addErrorMessage called (Redux):", {
        id: payload.id,
        message: payload.message.substring(0, 30) + (payload.message.length > 30 ? "..." : ""),
        timestamp: new Date().toISOString()
      });
      dispatch(addErrorMessage(payload));
    },
    clearMessages: () => {
      console.log("[DOUBLE_MSG_DEBUG] useChat.clearMessages called (Redux)");
      dispatch(clearMessages());
    },
  };
}