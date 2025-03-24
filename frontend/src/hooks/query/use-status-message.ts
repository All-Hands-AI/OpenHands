import { useState, useEffect } from "react";
import { getQueryReduxBridge } from "#/utils/query-redux-bridge";
import { StatusMessage } from "#/types/message";

// Initial status message
const initialStatusMessage: StatusMessage = {
  status_update: true,
  type: "info",
  id: "",
  message: "",
};

/**
 * Hook to access and manipulate status messages
 * This replaces the Redux status slice functionality without using React Query
 */
export function useStatusMessage() {
  const [statusMessage, setStatusMessageState] =
    useState<StatusMessage>(initialStatusMessage);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize from Redux on mount
  useEffect(() => {
    try {
      const bridge = getQueryReduxBridge();
      const reduxState = bridge.getReduxSliceState<{
        curStatusMessage: StatusMessage;
      }>("status");
      setStatusMessageState(reduxState.curStatusMessage);
    } catch (error) {
      // If we can't get the state from Redux, use the initial state
      // eslint-disable-next-line no-console
      console.warn("Could not get status message from Redux, using default");
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Function to update status message
  const setStatusMessage = (newStatusMessage: StatusMessage) => {
    // eslint-disable-next-line no-console
    console.log("[Status Debug] Setting status message:", {
      id: newStatusMessage.id,
      message: newStatusMessage.message,
      type: newStatusMessage.type,
    });

    setStatusMessageState(newStatusMessage);

    // eslint-disable-next-line no-console
    console.log("[Status Debug] Successfully set status message:", {
      id: newStatusMessage.id,
      message: newStatusMessage.message,
    });
  };

  return {
    statusMessage,
    isLoading,
    setStatusMessage,
  };
}
