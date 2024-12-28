import posthog from "posthog-js";
import React from "react";
import { io, Socket } from "socket.io-client";

import EventLogger from "#/utils/event-logger";
import { handleAssistantMessage } from "#/services/actions";
import { useRate } from "#/hooks/use-rate";

const isOpenHandsMessage = (event: Record<string, unknown>) =>
  event.action === "message";

export enum WsClientProviderStatus {
  CONNECTED,
  DISCONNECTED,
}

interface UseWsClient {
  status: WsClientProviderStatus;
  isLoadingMessages: boolean;
  events: Record<string, unknown>[];
  send: (event: Record<string, unknown>) => void;
}

const WsClientContext = React.createContext<UseWsClient>({
  status: WsClientProviderStatus.DISCONNECTED,
  isLoadingMessages: true,
  events: [],
  send: () => {
    throw new Error("not connected");
  },
});

interface WsClientProviderProps {
  conversationId: string;
  ghToken: string | null;
}

export function WsClientProvider({
  ghToken,
  conversationId,
  children,
}: React.PropsWithChildren<WsClientProviderProps>) {
  const sioRef = React.useRef<Socket | null>(null);
  const ghTokenRef = React.useRef<string | null>(ghToken);
  const [status, setStatus] = React.useState(
    WsClientProviderStatus.DISCONNECTED,
  );
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
    setStatus(WsClientProviderStatus.CONNECTED);
  }

  function handleMessage(event: Record<string, unknown>) {
    if (isOpenHandsMessage(event)) {
      messageRateHandler.record(new Date().getTime());
    }
    setEvents((prevEvents) => [...prevEvents, event]);
    if (!Number.isNaN(parseInt(event.id as string, 10))) {
      lastEventRef.current = event;
    }

    handleAssistantMessage(event);
  }

  function handleDisconnect() {
    setStatus(WsClientProviderStatus.DISCONNECTED);
    const sio = sioRef.current;
    if (!sio) {
      return;
    }
    sio.io.opts.query = sio.io.opts.query || {};
    sio.io.opts.query.latest_event_id = lastEventRef.current?.id;
  }

  function handleError() {
    posthog.capture("socket_error");
    setStatus(WsClientProviderStatus.DISCONNECTED);
  }

  React.useEffect(() => {
    if (!conversationId) {
      throw new Error("No conversation ID provided");
    }

    let sio = sioRef.current;

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
        github_token: ghToken || undefined,
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

    return () => {
      sio.off("connect", handleConnect);
      sio.off("oh_event", handleMessage);
      sio.off("connect_error", handleError);
      sio.off("connect_failed", handleError);
      sio.off("disconnect", handleDisconnect);
    };
  }, [ghToken, conversationId]);

  React.useEffect(
    () => () => {
      const sio = sioRef.current;
      if (sio) {
        sio.off("disconnect", handleDisconnect);
        sio.disconnect();
      }
    },
    [],
  );

  const value = React.useMemo<UseWsClient>(
    () => ({
      status,
      isLoadingMessages: messageRateHandler.isUnderThreshold,
      events,
      send,
    }),
    [status, messageRateHandler.isUnderThreshold, events],
  );

  return <WsClientContext value={value}>{children}</WsClientContext>;
}

export function useWsClient() {
  const context = React.useContext(WsClientContext);
  return context;
}
