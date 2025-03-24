import { combineReducers, configureStore, Middleware } from "@reduxjs/toolkit";
import { queryClient } from "./query-redux-bridge-init";
import type { Message } from "#/message";

// All slices are now handled by React Query

// Define a type for chat actions
type ChatAction = {
  type: string;
  payload?: any;
};

// Define a type for the chat state
interface ChatState {
  messages: Message[];
}

export const rootReducer = combineReducers({
  // All slices have been migrated to React Query
  // Adding a dummy chat reducer to handle actions during migration
  chat: (state: ChatState = { messages: [] }, action: ChatAction) => {
    switch (action.type) {
      case "chat/addUserMessage":
      case "chat/addAssistantMessage":
      case "chat/addAssistantAction":
      case "chat/addAssistantObservation":
      case "chat/addErrorMessage":
      case "chat/clearMessages":
        // These actions are now handled by the middleware
        return state;
      default:
        return state;
    }
  }
});

// Create a middleware to intercept Redux actions and update React Query
const reactQueryMiddleware: Middleware = () => (next) => (action: unknown) => {
  // Cast action to ChatAction for our internal use
  const chatAction = action as ChatAction;
  // Log all actions for debugging
  console.log("[Redux Middleware] Action:", chatAction.type);

  // Handle chat actions
  if (chatAction.type && typeof chatAction.type === 'string' && chatAction.type.startsWith("chat/")) {
    // Get current messages from React Query
    const currentMessages = queryClient.getQueryData<Message[]>(["chat", "messages"]) || [];
    
    switch (chatAction.type) {
      case "chat/addUserMessage": {
        const { content, imageUrls, timestamp, pending } = chatAction.payload;
        const message: Message = {
          type: "thought",
          sender: "user",
          content,
          imageUrls,
          timestamp,
          pending: !!pending,
        };
        console.log("[Redux Middleware] Adding user message to React Query");
        queryClient.setQueryData(["chat", "messages"], [...currentMessages, message]);
        break;
      }
      case "chat/addAssistantMessage": {
        const content = chatAction.payload;
        const message: Message = {
          type: "thought",
          sender: "assistant",
          content,
          imageUrls: [],
          timestamp: new Date().toISOString(),
        };
        console.log("[Redux Middleware] Adding assistant message to React Query");
        queryClient.setQueryData(["chat", "messages"], [...currentMessages, message]);
        break;
      }
      case "chat/addAssistantAction": {
        const actionPayload = chatAction.payload as any;
        // Find the appropriate message type based on the action
        const actionType = actionPayload.action;
        let translationID = `ACTION_MESSAGE$${actionType.toUpperCase()}`;
        let content = "";
        
        // Basic handling for common action types
        if (actionPayload.args && actionPayload.args.thought) {
          content = actionPayload.args.thought;
        } else if (actionType === "run" && actionPayload.args) {
          content = `Command:\n\`${actionPayload.args.command}\``;
        } else if (actionType === "run_ipython" && actionPayload.args) {
          content = `\`\`\`\n${actionPayload.args.code}\n\`\`\``;
        }
        
        const message: Message = {
          type: "action",
          sender: "assistant",
          translationID,
          eventID: actionPayload.id,
          content,
          imageUrls: [],
          timestamp: new Date().toISOString(),
        };
        
        console.log("[Redux Middleware] Adding assistant action to React Query");
        queryClient.setQueryData(["chat", "messages"], [...currentMessages, message]);
        break;
      }
      case "chat/addAssistantObservation": {
        const observation = chatAction.payload as any;
        // This is a simplified version - in a real implementation, you'd need to find
        // the corresponding action message and update it
        console.log("[Redux Middleware] Adding assistant observation to React Query");
        break;
      }
      case "chat/addErrorMessage": {
        const { id, message } = chatAction.payload as { id?: string; message: string };
        const errorMessage: Message = {
          translationID: id,
          content: message,
          type: "error",
          sender: "assistant",
          timestamp: new Date().toISOString(),
        };
        
        console.log("[Redux Middleware] Adding error message to React Query");
        queryClient.setQueryData(["chat", "messages"], [...currentMessages, errorMessage]);
        break;
      }
      case "chat/clearMessages":
        console.log("[Redux Middleware] Clearing messages in React Query");
        queryClient.setQueryData(["chat", "messages"], []);
        break;
    }
  }

  // Continue with the normal Redux flow
  return next(action);
};

const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) => 
    getDefaultMiddleware().concat(reactQueryMiddleware),
});

// Define a more flexible RootState type that includes test-specific slices
export interface RootState {
  chat: ChatState;
  // Include test-specific slices
  agent?: any;
  cmd?: any;
  // Add other test-specific slices as needed
}
export type AppStore = typeof store;
export type AppDispatch = typeof store.dispatch;

export default store;
