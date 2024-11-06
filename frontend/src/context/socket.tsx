import React from "react";
import { Data } from "ws";
import EventLogger from "#/utils/event-logger";

const RECONNECT_RETRIES = 5;

interface WebSocketClientOptions {
  token: string | null;
  onOpen?: (event: Event, isNewSession: boolean) => void;
  onMessage?: (event: MessageEvent<Data>) => void;
  onError?: (event: Event) => void;
  onClose?: (event: Event) => void;
}

interface WebSocketContextType {
  send: (data: string | ArrayBufferLike | Blob | ArrayBufferView) => void;
  start: (options?: WebSocketClientOptions) => void;
  stop: () => void;
  setRuntimeIsInitialized: (runtimeIsInitialized: boolean) => void;
  runtimeIsInitialized: boolean;
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
  const wsReconnectRetries = React.useRef<number>(RECONNECT_RETRIES);
  const [isConnected, setIsConnected] = React.useState(false);
  const [runtimeIsInitialized, setRuntimeIsInitialized] = React.useState(false);
  const [events, setEvents] = React.useState<Record<string, unknown>[]>([]);

  const start = React.useCallback((options?: WebSocketClientOptions): void => {
    if (wsRef.current) {
      EventLogger.warning(
        "WebSocket connection is already established, but a new one is starting anyways.",
      );
    }

    const baseUrl =
      import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const sessionToken = options?.token || "NO_JWT"; // not allowed to be empty or duplicated
    const ghToken = localStorage.getItem("ghToken") || "NO_GITHUB";

    const ws = new WebSocket(`${protocol}//${baseUrl}/ws`, [
      "openhands",
      sessionToken,
      ghToken,
    ]);

    ws.addEventListener("open", (event) => {
      setIsConnected(true);
      const isNewSession = sessionToken === "NO_JWT";
      wsReconnectRetries.current = RECONNECT_RETRIES;
      options?.onOpen?.(event, isNewSession);
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
      setRuntimeIsInitialized(false);
      wsRef.current = null;
      options?.onClose?.(event);
      if (wsReconnectRetries.current) {
        wsReconnectRetries.current -= 1;
        const token = localStorage.getItem("token");
        setTimeout(() => start({ ...(options || {}), token }), 1);
      }
    });

    wsRef.current = ws;
  }, []);

  const stop = React.useCallback((): void => {
    wsReconnectRetries.current = 0;
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
      setEvents((prevEvents) => [...prevEvents, JSON.parse(data.toString())]);
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
      runtimeIsInitialized,
      isConnected,
      events,
    }),
    [
      send,
      start,
      stop,
      setRuntimeIsInitialized,
      runtimeIsInitialized,
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
