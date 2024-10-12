import React from "react";
import { Data } from "ws";
import EventLogger from "#/utils/event-logger";
import { getValidFallbackHost } from "#/utils/get-valid-fallback-host";

interface WebSocketClientOptions {
  token: string | null;
  onOpen?: (event: Event) => void;
  onMessage?: (event: MessageEvent<Data>) => void;
  onError?: (event: Event) => void;
  onClose?: (event: Event) => void;
}

interface WebSocketContextType {
  send: (data: string | ArrayBufferLike | Blob | ArrayBufferView) => void;
  start: (options?: WebSocketClientOptions) => void;
  stop: () => void;
  setRuntimeIsInitialized: () => void;
  runtimeActive: boolean;
  isConnected: boolean;
  events: Record<string, unknown>[];
}

const SocketContext = React.createContext<WebSocketContextType | undefined>(
  undefined,
);

interface SocketProviderProps {
  children: React.ReactNode;
}

function SocketProvider({ children }: SocketProviderProps) {
  const wsRef = React.useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = React.useState(false);
  const [runtimeActive, setRuntimeActive] = React.useState(false);
  const [events, setEvents] = React.useState<Record<string, unknown>[]>([]);

  const setRuntimeIsInitialized = () => {
    setRuntimeActive(true);
  };

  const start = React.useCallback((options?: WebSocketClientOptions): void => {
    if (wsRef.current) {
      EventLogger.warning(
        "WebSocket connection is already established, but a new one is starting anyways.",
      );
    }

    const fallback = getValidFallbackHost();
    const baseUrl = import.meta.env.VITE_BACKEND_BASE_URL || fallback;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(
      `${protocol}//${baseUrl}/ws${options?.token ? `?token=${options.token}` : ""}`,
    );

    ws.addEventListener("open", (event) => {
      setIsConnected(true);
      options?.onOpen?.(event);
    });

    ws.addEventListener("message", (event) => {
      EventLogger.message(event);

      setEvents((prevEvents) => [...prevEvents, JSON.parse(event.data)]);
      options?.onMessage?.(event);
    });

    ws.addEventListener("error", (event) => {
      EventLogger.event(event, "SOCKET ERROR");
      options?.onError?.(event);
    });

    ws.addEventListener("close", (event) => {
      EventLogger.event(event, "SOCKET CLOSE");

      setIsConnected(false);
      setRuntimeActive(false);
      wsRef.current = null;
      options?.onClose?.(event);
    });

    wsRef.current = ws;
  }, []);

  const stop = React.useCallback((): void => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = React.useCallback(
    (data: string | ArrayBufferLike | Blob | ArrayBufferView) => {
      if (!wsRef.current) {
        EventLogger.error("WebSocket is not connected.");
        return;
      }
      wsRef.current.send(data);
    },
    [],
  );

  const value = React.useMemo(
    () => ({
      send,
      start,
      stop,
      setRuntimeIsInitialized,
      runtimeActive,
      isConnected,
      events,
    }),
    [
      send,
      start,
      stop,
      setRuntimeIsInitialized,
      runtimeActive,
      isConnected,
      events,
    ],
  );

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
