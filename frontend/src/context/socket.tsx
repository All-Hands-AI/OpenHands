import React from "react";
import { WebSocketClientReturnType } from "#/hooks/useWebSocketClient";

type SocketContextType = {
  socket: WebSocketClientReturnType;
};

const SocketContext = React.createContext<SocketContextType | undefined>(
  undefined,
);

interface SocketProviderProps {
  children: React.ReactNode;
  socket: WebSocketClientReturnType;
}

function SocketProvider({ children, socket }: SocketProviderProps) {
  const value = React.useMemo(() => ({ socket }), [socket]);

  return (
    <SocketContext.Provider value={value}>{children}</SocketContext.Provider>
  );
}

function useSocket() {
  const context = React.useContext(SocketContext);
  if (context === undefined) {
    throw new Error("useSocket must be used within a SocketProvider");
  }
  return context;
}

export { SocketProvider, useSocket };
