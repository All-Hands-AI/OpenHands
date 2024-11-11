import posthog from "posthog-js";
import React from "react";
import { Settings } from "#/services/settings";
import ActionType from "#/types/ActionType";
import EventLogger from "#/utils/event-logger";
import AgentState from "#/types/AgentState";

export enum WsClientProviderStatus {
  STOPPED,
  OPENING,
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
  const tokenRef = React.useRef<string | null>(token);
  const ghTokenRef = React.useRef<string | null>(ghToken);
  const closeRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const [status, setStatus] = React.useState(WsClientProviderStatus.STOPPED);
  const [events, setEvents] = React.useState<Record<string, unknown>[]>([]);

  function send(event: Record<string, unknown>) {
    if (!wsRef.current) {
      EventLogger.error("WebSocket is not connected.");
      return;
    }
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
    setStatus(WsClientProviderStatus.ERROR);
  }

  // Connect websocket
  React.useEffect(() => {
    let ws = wsRef.current;

    // If disabled close any existing websockets...
    if (!enabled) {
      if (ws) {
        ws.close();
      }
      wsRef.current = null;
      return () => {};
    }

    // If there is no websocket or the tokens have changed or the current websocket is closed,
    // create a new one
    if (
      !ws ||
      (tokenRef.current && token !== tokenRef.current) ||
      ghToken !== ghTokenRef.current ||
      ws.readyState === WebSocket.CLOSED ||
      ws.readyState === WebSocket.CLOSING
    ) {
      ws?.close();
      const baseUrl =
        import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host;
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      ws = new WebSocket(`${protocol}//${baseUrl}/ws`, [
        "openhands",
        token || "NO_JWT",
        ghToken || "NO_GITHUB",
      ]);
    }
    ws.addEventListener("open", handleOpen);
    ws.addEventListener("message", handleMessage);
    ws.addEventListener("error", handleError);
    ws.addEventListener("close", handleClose);
    wsRef.current = ws;
    tokenRef.current = token;
    ghTokenRef.current = ghToken;

    return () => {
      ws.removeEventListener("open", handleOpen);
      ws.removeEventListener("message", handleMessage);
      ws.removeEventListener("error", handleError);
      ws.removeEventListener("close", handleClose);
    };
  }, [enabled, token, ghToken]);

  // Strict mode mounts and unmounts each component twice, so we have to wait in the destructor
  // before actually closing the socket and cancel the operation if the component gets remounted.
  React.useEffect(() => {
    const timeout = closeRef.current;
    if (timeout != null) {
      clearTimeout(timeout);
    }

    return () => {
      closeRef.current = setTimeout(() => {
        wsRef.current?.close();
      }, 100);
    };
  }, []);

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
