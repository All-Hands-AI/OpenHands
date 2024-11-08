import posthog from "posthog-js";
import React from "react";
import { Settings } from "#/services/settings";
import ActionType from "#/types/ActionType";
import EventLogger from "#/utils/event-logger";

export enum WsClientProviderStatus {
  STOPPED,
  OPENING,
  INITIALIZING,
  READY,
}

interface UseWsClient {
  status: WsClientProviderStatus;
  events: Record<string, unknown>[];
  send: (event: Record<string, unknown>) => void;
}

const WsClientContext = React.createContext<UseWsClient>({
  status: WsClientProviderStatus.STOPPED,
  events: [],
  send: () => {
    throw new Error("not connected");
  },
});

interface WsClientProviderProps {
  enabled: boolean;
  token: string | null;
  ghToken: string | null;
  settings: Settings;
}

export function WsClientProvider({
  enabled,
  token,
  ghToken,
  settings,
  children,
}: React.PropsWithChildren<WsClientProviderProps>) {
  const wsRef = React.useRef<WebSocket | null>(null);
  const [status, setStatus] = React.useState(WsClientProviderStatus.STOPPED);
  const [events, setEvents] = React.useState<Record<string, unknown>[]>([]);

  function send(event: Record<string, unknown>) {
    if (!wsRef.current) {
      EventLogger.error("WebSocket is not connected.");
      return;
    }
    setEvents((prevEvents) => [...prevEvents, event]);
    wsRef.current.send(JSON.stringify(event));
  }

  function handleOpen() {
    const initEvent = {
      action: ActionType.INIT,
      args: settings,
    };
    send(initEvent);
  }

  function handleMessage(event: MessageEvent) {
    setEvents([...events, JSON.parse(event.data)]);
  }

  function handleClose() {
    setStatus(WsClientProviderStatus.STOPPED);
    setEvents([]);
    wsRef.current = null;
  }

  function handleError(event: Event) {
    posthog.capture("socket_error");
    EventLogger.event(event, "SOCKET ERROR");
  }

  // Connect / disconnect websocket
  React.useEffect(() => {
    if (!enabled) {
      const ws = wsRef.current;
      if (ws) {
        ws.close();
      }
      wsRef.current = null;
      return;
    }
    let ws = wsRef.current;
    if (ws) {
      ws.close();
    }
    const baseUrl =
      import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${protocol}//${baseUrl}/ws`, [
      "openhands",
      token || "NO_JWT",
      ghToken || "NO_GITHUB",
    ]);
    ws.addEventListener("open", handleOpen);
    ws.addEventListener("message", handleMessage);
    ws.addEventListener("error", handleError);
    ws.addEventListener("close", handleClose);
    wsRef.current = ws;
  }, [enabled, token, ghToken, settings]);

  const value = React.useMemo<UseWsClient>(
    () => ({
      status,
      events,
      send,
    }),
    [status, events],
  );

  return (
    <WsClientContext.Provider value={value}>
      {children}
    </WsClientContext.Provider>
  );
}

export function useWsClient() {
  const context = React.useContext(WsClientContext);
  return context;
}
