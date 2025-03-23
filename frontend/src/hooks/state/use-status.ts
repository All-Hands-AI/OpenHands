import { useState, useCallback } from "react";
import { StatusMessage } from "#/types/message";

const initialStatusMessage: StatusMessage = {
  status_update: true,
  type: "info",
  id: "",
  message: "",
};

/**
 * Custom hook for managing status messages
 * This replaces the Redux status-slice
 */
export function useStatus() {
  const [curStatusMessage, setCurStatusMessage] =
    useState<StatusMessage>(initialStatusMessage);

  /**
   * Set the current status message
   */
  const updateStatusMessage = useCallback((message: StatusMessage) => {
    setCurStatusMessage(message);
  }, []);

  /**
   * Clear the current status message
   */
  const clearStatusMessage = useCallback(() => {
    setCurStatusMessage(initialStatusMessage);
  }, []);

  return {
    curStatusMessage,
    updateStatusMessage,
    clearStatusMessage,
  };
}
