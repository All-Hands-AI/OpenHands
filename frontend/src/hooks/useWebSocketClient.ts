import type { Data } from "ws";
import React from "react";
import { useEffectOnce } from "#/utils/use-effect-once";

interface WebSocketClientOptions {
  token: string | null;
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
  const wsRef = React.useRef<WebSocket>();

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
