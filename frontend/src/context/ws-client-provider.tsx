import posthog from "posthog-js";
import React from "react";
import { io, Socket } from "socket.io-client";
import { Settings } from "#/services/settings";
import ActionType from "#/types/ActionType";
import EventLogger from "#/utils/event-logger";
import AgentState from "#/types/AgentState";
import { handleAssistantMessage } from "#/services/actions";

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
  const sioRef = React.useRef<Socket | null>(null);
  const tokenRef = React.useRef<string | null>(token);
  const ghTokenRef = React.useRef<string | null>(ghToken);
  const disconnectRef = React.useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const [status, setStatus] = React.useState(WsClientProviderStatus.STOPPED);
  const [events, setEvents] = React.useState<Record<string, unknown>[]>([]);

  function send(event: Record<string, unknown>) {
    if (!sioRef.current) {
      EventLogger.error("WebSocket is not connected.");
      return;
    }
    sioRef.current.emit("oh_action", event);
  }

  function handleConnect() {
    console.log("TRACE:connect");
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
    if (events.length) {
      initEvent.latest_event_id = `${events[events.length - 1].id}`;
    }
    send(initEvent);
  }

  function handleMessage(event: Record<string, unknown>) {
    setEvents((prevEvents) => [...prevEvents, event]);
    const extras = event.extras as Record<string, unknown>;
    if (extras?.agent_state === AgentState.INIT) {
      setStatus(WsClientProviderStatus.ACTIVE);
    }
    if (
      status !== WsClientProviderStatus.ACTIVE &&
      event?.observation === "error"
    ) {
      setStatus(WsClientProviderStatus.ERROR);
    }

    if (!event.token) {
      handleAssistantMessage(event);
    }
  }

  function handleDisconnect() {
    setStatus(WsClientProviderStatus.STOPPED);
    setEvents([]);
    sioRef.current = null;
  }

  function handleError() {
    console.log("TRACE:SIO:Error");
    posthog.capture("socket_error");
    setStatus(WsClientProviderStatus.ERROR);
    sioRef.current?.disconnect();
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
      (tokenRef.current && token !== tokenRef.current) ||
      ghToken !== ghTokenRef.current
    ) {
      sio?.disconnect();

      /*
      const extraHeaders: Record<string, string> = {};
      if (token) {
        extraHeaders.token = token;
      }
      if (ghToken) {
        extraHeaders.github_token = ghToken;
      }
      if (events.length) {
        extraHeaders.latest_event_id = `${events[events.length - 1].id}`;
      }
      */

      const baseUrl =
        import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host;
      sio = io(baseUrl, {
        transports: ["websocket"],
        // extraHeaders: {
        //  Testy: "TESTER"
        // },
        // We force a new connection, because the headers may have changed.
        // forceNew: true,

        // Had to do this for now because reconnection actually starts a new session,
        // which we don't want - The reconnect has the same headers as the original
        // which don't include the original session id
        // reconnection: false,
        // reconnectionDelay: 1000,
        // reconnectionDelayMax : 5000,
        // reconnectionAttempts: 5
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
