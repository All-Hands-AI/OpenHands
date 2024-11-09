import posthog from "posthog-js";
import React from "react";
import { Settings } from "#/services/settings";
import ActionType from "#/types/ActionType";
import EventLogger from "#/utils/event-logger";
import AgentState from "#/types/AgentState";

export enum WsClientProviderStatus {
  STOPPED,
  OPENING,
  INITIALIZING,
  ACTIVE,
  ERROR,
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
  settings: Settings | null;
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
    // setEvents((prevEvents) => [...prevEvents, event]);
    wsRef.current.send(JSON.stringify(event));
  }

  function handleOpen() {
    setStatus(WsClientProviderStatus.OPENING);
    const initEvent = {
      action: ActionType.INIT,
      args: settings,
    };
    send(initEvent);
  }

  function handleMessage(messageEvent: MessageEvent) {
    const event = JSON.parse(messageEvent.data);
    setEvents((prevEvents) => [...prevEvents, event]);
    if (event.extras?.agent_state === AgentState.INIT) {
      setStatus(WsClientProviderStatus.ACTIVE);
    }
    if (
      status !== WsClientProviderStatus.ACTIVE &&
      event?.observation === "error"
    ) {
      setStatus(WsClientProviderStatus.ERROR);
    }
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
    if (
      ws &&
      ws.readyState !== WebSocket.CLOSING &&
      ws.readyState !== WebSocket.CLOSED
    ) {
      // This is really annoying. StrictMode means this hook is called twice with no change.
      return;
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
  }, [enabled, token, ghToken]);

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
