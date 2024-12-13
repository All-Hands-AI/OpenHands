import posthog from "posthog-js";
import React from "react";
import { io, Socket } from "socket.io-client";

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
  conversationId: string;
  ghToken: string | null;
  selectedRepository: string | null;
}

export function WsClientProvider({
  enabled,
  ghToken,
  selectedRepository,
  conversationId,
  children,
}: React.PropsWithChildren<WsClientProviderProps>) {
  const sioRef = React.useRef<Socket | null>(null);
  const ghTokenRef = React.useRef<string | null>(ghToken);
  const selectedRepositoryRef = React.useRef<string | null>(selectedRepository);
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
  }

  function handleMessage(event: Record<string, unknown>) {
    if (isOpenHandsMessage(event)) {
      messageRateHandler.record(new Date().getTime());
    }
    setEvents((prevEvents) => [...prevEvents, event]);
    if (!Number.isNaN(parseInt(event.id as string, 10))) {
      lastEventRef.current = event;
    }
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

    handleAssistantMessage(event);
  }

  function handleDisconnect() {
    setStatus(WsClientProviderStatus.STOPPED);
  }

  function handleError() {
    posthog.capture("socket_error");
    setStatus(WsClientProviderStatus.ERROR);
  }

  React.useEffect(() => {
    if (!conversationId) {
      throw new Error("No conversation ID provided");
    }

    let sio = sioRef.current;

    if (!enabled) {
      if (sio) {
        sio.disconnect();
      }
      return () => {};
    }

    const lastEvent = lastEventRef.current;
    const query = {
      latest_event_id: lastEvent?.id ?? -1,
      conversation_id: conversationId,
    };

    const baseUrl =
      import.meta.env.VITE_BACKEND_BASE_URL || window?.location.host;

    sio = io(baseUrl, {
      transports: ["websocket"],
      auth: {
        githubToken: ghToken || undefined,
      },
      query,
    });
    sio.on("connect", handleConnect);
    sio.on("oh_event", handleMessage);
    sio.on("connect_error", handleError);
    sio.on("connect_failed", handleError);
    sio.on("disconnect", handleDisconnect);

    sioRef.current = sio;
    ghTokenRef.current = ghToken;
    selectedRepositoryRef.current = selectedRepository;

    return () => {
      sio.off("connect", handleConnect);
      sio.off("oh_event", handleMessage);
      sio.off("connect_error", handleError);
      sio.off("connect_failed", handleError);
      sio.off("disconnect", handleDisconnect);
    };
  }, [enabled, ghToken, selectedRepository, conversationId]);

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
