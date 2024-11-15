import posthog from "posthog-js";
import React from "react";
import { Settings } from "#/services/settings";
import ActionType from "#/types/ActionType";
import EventLogger from "#/utils/event-logger";
import AgentState from "#/types/AgentState";
import { handleAssistantMessage } from "#/services/actions";
import { useRate } from "#/utils/use-rate";

const isOpenHandsMessage = (event: Record<string, unknown>) =>
  event.action === "message";

const RECONNECT_RETRIES = 5;

export enum WsClientProviderStatus {
  STOPPED,
  OPENING,
  ACTIVE,
  ERROR,
}

interface UseWsClient {
  status: WsClientProviderStatus;
  isLoadingMessages: boolean;
  events: Record<string, unknown>[];
  send: (event: Record<string, unknown>) => void;
}

const WsClientContext = React.createContext<UseWsClient>({
  status: WsClientProviderStatus.STOPPED,
  isLoadingMessages: true,
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
  const [retryCount, setRetryCount] = React.useState(RECONNECT_RETRIES);

  const messageRateHandler = useRate({ threshold: 500 });

  function send(event: Record<string, unknown>) {
    if (!wsRef.current) {
      EventLogger.error("WebSocket is not connected.");
      return;
    }
    wsRef.current.send(JSON.stringify(event));
  }

  function handleOpen() {
    setRetryCount(RECONNECT_RETRIES);
    setStatus(WsClientProviderStatus.OPENING);
    const initEvent = {
      action: ActionType.INIT,
      args: settings,
    };
    send(initEvent);
  }

  function handleMessage(messageEvent: MessageEvent) {
    const event = JSON.parse(messageEvent.data);
    if (isOpenHandsMessage(event)) {
      messageRateHandler.record(new Date().getTime());
    }
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

    handleAssistantMessage(event);
  }

  function handleClose() {
    if (retryCount) {
      setTimeout(() => {
        setRetryCount(retryCount - 1);
      }, 1000);
    } else {
      setStatus(WsClientProviderStatus.STOPPED);
      setEvents([]);
    }
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
    if (!enabled || !retryCount) {
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
      let wsUrl = `${protocol}//${baseUrl}/ws`;
      if (events.length) {
        wsUrl += `?latest_event_id=${events[events.length - 1].id}`;
      }
      ws = new WebSocket(wsUrl, [
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
  }, [enabled, token, ghToken, retryCount]);

  // Strict mode mounts and unmounts each component twice, so we have to wait in the destructor
  // before actually closing the socket and cancel the operation if the component gets remounted.
  React.useEffect(() => {
    const timeout = closeRef.current;
    if (timeout != null) {
      clearTimeout(timeout);
    }

    return () => {
      closeRef.current = setTimeout(() => {
        const ws = wsRef.current;
        if (ws) {
          ws.removeEventListener("close", handleClose);
          ws.close();
        }
      }, 100);
    };
  }, []);

  const value = React.useMemo<UseWsClient>(
    () => ({
      status,
      isLoadingMessages: messageRateHandler.isUnderThreshold,
      events,
      send,
    }),
    [status, messageRateHandler.isUnderThreshold, events],
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
