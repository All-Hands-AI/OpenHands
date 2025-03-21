import { useEffect, useRef } from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { Message } from "#/message";

type ActionType =
  | "run"
  | "run_ipython"
  | "write"
  | "read"
  | "browse"
  | "edit"
  | "think"
  | "finish";

type ActionEventCallback = (message: Message) => void;

/**
 * Hook to subscribe to specific action events in the chat
 * @param actionType The type of action to listen for (e.g., "run", "browse")
 * @param callback Function to call when the action is detected
 */
export const useActionEvents = (
  actionType: ActionType | ActionType[],
  callback: ActionEventCallback,
) => {
  const messages = useSelector((state: RootState) => state.chat.messages);
  const prevMessagesLengthRef = useRef(messages.length);
  const actionTypes = Array.isArray(actionType) ? actionType : [actionType];

  // Helper function to detect if a message is a specific action type
  const isActionOfType = (message: Message, type: ActionType): boolean => {
    if (message.type !== "action" || message.sender !== "assistant") {
      return false;
    }

    // Detect action type based on content patterns
    switch (type) {
      case "run":
        return message.content.startsWith("Command:\n`");
      case "run_ipython":
        return message.content.startsWith("```\n");
      case "browse":
        return message.content.startsWith("Browsing ");
      case "write":
      case "read":
      case "edit":
      case "think":
      case "finish":
        // These could be enhanced with more specific patterns if needed
        return message.translationID === `ACTION_MESSAGE$${type.toUpperCase()}`;
      default:
        return false;
    }
  };

  useEffect(() => {
    // Check if messages length increased (new message added)
    if (messages.length > prevMessagesLengthRef.current) {
      // Look at only the new messages
      const newMessages = messages.slice(prevMessagesLengthRef.current);

      // Find any messages that match the action types we're looking for
      newMessages.forEach((message) => {
        if (actionTypes.some((type) => isActionOfType(message, type))) {
          callback(message);
        }
      });
    }

    // Update the ref for next comparison
    prevMessagesLengthRef.current = messages.length;
  }, [messages, actionTypes, callback]);
};
