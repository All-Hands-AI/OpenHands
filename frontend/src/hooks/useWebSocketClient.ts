import { useEffect, useRef } from "react";
import type { Data } from "ws";

// Introduce this custom React hook to run any given effect
// ONCE. In Strict mode, React will run all useEffect's twice,
// which will trigger a WebSocket connection and then immediately
// close it, causing the "closed before could connect" error.
function useEffectOnce(callback: () => void) {
  const isUsedRef = useRef(false);

  useEffect(() => {
    if (isUsedRef.current) {
      return;
    }

    isUsedRef.current = true;
    callback();
  }, [isUsedRef.current]);
}

interface WebSocketClientOptions {
  token?: string;
  onOpen?: (event: Event) => void;
  onMessage?: (event: MessageEvent<Data>) => void;
  onError?: (event: Event) => void;
  onClose?: (event: Event) => void;
}

export interface WebSocketClientReturnType {
  send: (data: string | ArrayBufferLike | Blob | ArrayBufferView) => void;
}

export function useWebSocketClient(
  options?: WebSocketClientOptions,
): WebSocketClientReturnType {
  const wsRef = useRef<WebSocket>();

  useEffectOnce(() => {
    const wsUrl = new URL("/", document.baseURI);
    wsUrl.protocol = wsUrl.protocol.replace("http", "ws");
    if (options?.token) wsUrl.searchParams.set("token", options.token);
    const ws = new WebSocket(`${wsUrl.origin}/ws`);

    if (options?.onOpen) {
      ws.addEventListener("open", options.onOpen);
    }
    if (options?.onMessage) {
      ws.addEventListener("message", options.onMessage);
    }
    if (options?.onError) {
      ws.addEventListener("error", options.onError);
    }
    if (options?.onClose) {
      ws.addEventListener("close", options.onClose);
    }

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  });

  return {
    send(data) {
      wsRef.current?.send(data);
    },
  };
}
