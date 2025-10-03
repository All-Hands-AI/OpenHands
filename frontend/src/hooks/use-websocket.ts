import React from "react";

export const useWebSocket = (
  url: string,
  options?: { queryParams?: Record<string, string> },
) => {
  const [isConnected, setIsConnected] = React.useState(false);
  const [lastMessage, setLastMessage] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<string[]>([]);
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

    ws.onopen = () => {
      setIsConnected(true);
      setError(null); // Clear any previous errors
    };

    ws.onmessage = (event) => {
      setLastMessage(event.data);
      setMessages((prev) => [...prev, event.data]);
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
      }
    };

    ws.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [url, options]);

  return {
    isConnected,
    lastMessage,
    messages,
    error,
    socket: wsRef.current,
  };
};
