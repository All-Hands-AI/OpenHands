import React from "react";

export const useWebSocket = <T = string>(
  url: string,
  options?: {
    queryParams?: Record<string, string>;
    onOpen?: (event: Event) => void;
    onClose?: (event: CloseEvent) => void;
    onMessage?: (event: MessageEvent) => void;
    onError?: (event: Event) => void;
  },
) => {
  const [isConnected, setIsConnected] = React.useState(false);
  const [lastMessage, setLastMessage] = React.useState<T | null>(null);
  const [messages, setMessages] = React.useState<T[]>([]);
  const [error, setError] = React.useState<Error | null>(null);
  const wsRef = React.useRef<WebSocket | null>(null);

  React.useEffect(() => {
    // Build URL with query parameters if provided
    let wsUrl = url;
    if (options?.queryParams) {
      const params = new URLSearchParams(options.queryParams);
      wsUrl = `${url}?${params.toString()}`;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = (event) => {
      setIsConnected(true);
      setError(null); // Clear any previous errors
      options?.onOpen?.(event);
    };

    ws.onmessage = (event) => {
      setLastMessage(event.data);
      setMessages((prev) => [...prev, event.data]);
      options?.onMessage?.(event);
    };

    ws.onclose = (event) => {
      setIsConnected(false);
      // If the connection closes with an error code, treat it as an error
      if (event.code !== 1000) {
        // 1000 is normal closure
        setError(
          new Error(
            `WebSocket closed with code ${event.code}: ${event.reason || "Connection closed unexpectedly"}`,
          ),
        );
        // Also call onError handler for error closures
        options?.onError?.(event);
      }
      options?.onClose?.(event);
    };

    ws.onerror = (event) => {
      setIsConnected(false);
      options?.onError?.(event);
    };

    return () => {
      ws.close();
    };
  }, [url, options]);

  const sendMessage = React.useCallback(
    (data: string | ArrayBufferLike | Blob | ArrayBufferView) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(data);
      }
    },
    [],
  );

  return {
    isConnected,
    lastMessage,
    messages,
    error,
    socket: wsRef.current,
    sendMessage,
  };
};
