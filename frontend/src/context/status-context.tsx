import React, { createContext, useContext, ReactNode, useEffect } from "react";
import { useStatus } from "#/hooks/state/use-status";
import { StatusMessage } from "#/types/message";
import { registerStatusService } from "#/services/context-services/status-service";

interface StatusContextType {
  curStatusMessage: StatusMessage;
  updateStatusMessage: (message: StatusMessage) => void;
  clearStatusMessage: () => void;
}

const StatusContext = createContext<StatusContextType | undefined>(undefined);

/**
 * Provider component for status messages
 */
export function StatusProvider({ children }: { children: ReactNode }) {
  const statusState = useStatus();

  // Register the update function with the service
  useEffect(() => {
    registerStatusService(statusState.updateStatusMessage);
  }, [statusState.updateStatusMessage]);

  return (
    <StatusContext.Provider value={statusState}>
      {children}
    </StatusContext.Provider>
  );
}

/**
 * Hook to use the status context
 */
export function useStatusContext() {
  const context = useContext(StatusContext);

  if (context === undefined) {
    throw new Error("useStatusContext must be used within a StatusProvider");
  }

  return context;
}
