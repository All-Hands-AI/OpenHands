import { useState, useEffect, useRef, useCallback } from "react";
import { io, Socket } from "socket.io-client";

interface UseSocketIOOptions {
  url: string;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
  reconnectionDelayMax?: number;
  timeout?: number;
  query?: Record<string, any>;
  path?: string;
  namespace?: string;
}

interface UseSocketIOReturn {
  socket: Socket | null;
  isConnected: boolean;
  isConnecting: boolean;
  connect: (options: UseSocketIOOptions) => void;
  disconnect: () => void;
  emit: <T>(event: string, ...args: T[]) => void;
  error: Error | null;
}

/**
 * A custom React hook to manage Socket.IO connections
 *
 * @param options Configuration options for the Socket.IO connection
 * @returns An object containing the socket instance and helper methods
 */
export const useSocketIO = (
  eventHandlers?: Record<string, (data: string) => void>,
): UseSocketIOReturn => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const socketRef = useRef<Socket | null>(null);

  const initSocket = useCallback(
    (options: UseSocketIOOptions) => {
      try {
        const {
          url,
          reconnectionAttempts = 5,
          reconnectionDelay = 1000,
          reconnectionDelayMax = 5000,
          timeout = 20000,
          query = {},
          path = "/socket.io",
          namespace = "",
        } = options;

        const fullUrl = namespace ? `${url}/${namespace}` : url;
        console.warn("Connecting to socket at:", options);

        socketRef.current = io(fullUrl, {
          transports: ["websocket"],
          reconnectionAttempts,
          reconnectionDelay,
          reconnectionDelayMax,
          timeout,
          query,
          path,
        });

        console.warn("REF", socketRef.current);

        // Set up event listeners
        socketRef.current.on("connect", () => {
          console.warn("CONNECTED!");
          setIsConnected(true);
          setIsConnecting(false);
          setError(null);
        });

        socketRef.current.on("disconnect", () => {
          console.warn("DISCONNECTED!");
          setIsConnected(false);
        });

        socketRef.current.on("connect_error", (err) => {
          console.warn("CONNECT_ERROR:", err);
          setError(err);
          setIsConnecting(false);
        });

        socketRef.current.on("reconnect_failed", () => {
          setError(new Error("Failed to reconnect after maximum attempts"));
          setIsConnecting(false);
        });

        // Register custom event handlers
        console.warn("Registering event handlers:", eventHandlers);
        Object.entries(eventHandlers || {}).forEach(([event, handler]) => {
          socketRef.current?.on(event, handler);
        });
      } catch (err) {
        console.warn("Error initializing socket:", err);
        setError(
          err instanceof Error
            ? err
            : new Error("Unknown error initializing socket"),
        );
        setIsConnecting(false);
      }
    },
    [eventHandlers],
  );

  const connect = useCallback(
    (options: UseSocketIOOptions) => {
      console.warn("Connecting to socket...", options.query);
      if (!socketRef.current) {
        initSocket(options);
        return;
      }

      if (!socketRef.current.connected) {
        setIsConnecting(true);
        socketRef.current.connect();
      }
    },
    [initSocket],
  );

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
    }
  }, []);

  // Emit event to socket server
  const emit = useCallback(<T>(event: string, ...args: T[]) => {
    if (socketRef.current) {
      socketRef.current.emit(event, ...args);
    } else {
      console.warn("Socket not initialized, cannot emit event:", event);
    }
  }, []);

  useEffect(
    () => () => {
      console.warn("Cleaning up socket connection...");

      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current.removeAllListeners();
        socketRef.current = null;
      }
    },
    [],
  );

  return {
    socket: socketRef.current,
    isConnected,
    isConnecting,
    connect,
    disconnect,
    emit,
    error,
  };
};
