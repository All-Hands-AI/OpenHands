import posthog from "posthog-js";
import React from "react";
import { io, Socket } from "socket.io-client";
import { Settings } from "#/services/settings";
import ActionType from "#/types/action-type";
import EventLogger from "#/utils/event-logger";
import AgentState from "#/types/agent-state";
import { handleAssistantMessage } from "#/services/actions";
import { useRate } from "#/hooks/use-rate";

const isOpenHandsMessage = (event: Record<string, unknown>) =>
  event.action === "message";

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
  const sioRef = React.useRef<Socket | null>(null);
  const tokenRef = React.useRef<string | null>(token);
  const ghTokenRef = React.useRef<string | null>(ghToken);
  const disconnectRef = React.useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const [status, setStatus] = React.useState(WsClientProviderStatus.STOPPED);
  const [events, setEvents] = React.useState<Record<string, unknown>[]>([]);
  const lastEventRef = React.useRef<Record<string, unknown> | null>(null);

  const messageRateHandler = useRate({ threshold: 250 });

  function send(event: Record<string, unknown>) {
    if (!sioRef.current) {
      EventLogger.error("WebSocket is not connected.");
      return;
    }
    sioRef.current.emit("oh_action", event);
  }

  function handleConnect() {
    setStatus(WsClientProviderStatus.OPENING);

    const initEvent: Record<string, unknown> = {
      action: ActionType.INIT,
      args: settings,
    };
    if (token) {
      initEvent.token = token;
    }
    if (ghToken) {
      initEvent.github_token = ghToken;
    }
    const lastEvent = lastEventRef.current;
    if (lastEvent && !Number.isNaN(parseInt(lastEvent.id as string, 10))) {
      initEvent.latest_event_id = lastEvent.id;
    }
    send(initEvent);
  }

  function handleMessage(event: Record<string, unknown>) {
    if (isOpenHandsMessage(event)) {
      messageRateHandler.record(new Date().getTime());
    }
    setEvents((prevEvents) => [...prevEvents, event]);
    lastEventRef.current = event;
    const extras = event.extras as Record<string, unknown>;
    if (extras?.agent_state === AgentState.INIT) {
      setStatus(WsClientProviderStatus.ACTIVE);
    }
    if (
      status !== WsClientProviderStatus.ACTIVE &&
      event?.observation === "error"
    ) {
      setStatus(WsClientProviderStatus.ERROR);
      return;
    }

    if (!event.token) {
      handleAssistantMessage(event);
    }
  }

  function handleDisconnect() {
    setStatus(WsClientProviderStatus.STOPPED);
  }

  function handleError() {
    posthog.capture("socket_error");
    setStatus(WsClientProviderStatus.ERROR);
  }

  // Connect websocket
  React.useEffect(() => {
    let sio = sioRef.current;

    // If disabled disconnect any existing websockets...
    if (!enabled) {
      if (sio) {
        sio.disconnect();
      }
      return () => {};
    }

    // If there is no websocket or the tokens have changed or the current websocket is disconnected,
    // create a new one
    if (
      !sio ||
      (tokenRef.current && token && token !== tokenRef.current) ||
      ghToken !== ghTokenRef.current
    ) {
      sio?.disconnect();

      const baseUrl =
        import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host;
      sio = io(baseUrl, {
        transports: ["websocket"],
      });
    }
    sio.on("connect", handleConnect);
    sio.on("oh_event", handleMessage);
    sio.on("connect_error", handleError);
    sio.on("connect_failed", handleError);
    sio.on("disconnect", handleDisconnect);

    sioRef.current = sio;
    tokenRef.current = token;
    ghTokenRef.current = ghToken;

    return () => {
      sio.off("connect", handleConnect);
      sio.off("oh_event", handleMessage);
      sio.off("connect_error", handleError);
      sio.off("connect_failed", handleError);
      sio.off("disconnect", handleDisconnect);
    };
  }, [enabled, token, ghToken]);

  // Strict mode mounts and unmounts each component twice, so we have to wait in the destructor
  // before actually disconnecting the socket and cancel the operation if the component gets remounted.
  React.useEffect(() => {
    const timeout = disconnectRef.current;
    if (timeout != null) {
      clearTimeout(timeout);
    }

    return () => {
      disconnectRef.current = setTimeout(() => {
        const sio = sioRef.current;
        if (sio) {
          sio.off("disconnect", handleDisconnect);
          sio.disconnect();
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
