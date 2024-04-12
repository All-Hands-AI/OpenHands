// import { toast } from "sonner";
import { handleAssistantMessage } from "./actions";
import { getToken } from "./auth";
import toast from "../utils/toast";

class Socket {
  private static _socket: WebSocket | null = null;

  // callbacks contain a list of callable functions
  // event: function, like:
  // open: [function1, function2]
  // message: [function1, function2]
  private static callbacks: {
    [K in keyof WebSocketEventMap]: ((data: WebSocketEventMap[K]) => void)[];
  } = {
    open: [],
    message: [],
    error: [],
    close: [],
  };

  // prevent it failed in the first run, all related listen events never be called
  private static isFirstRun = true;

  public static tryInitialize(): void {
    getToken()
      .then((token) => {
        Socket._initialize(token);
      })
      .catch(() => {
        const msg = `Connection failed. Retry...`;
        toast.stickyError("ws", msg);

        if (this.isFirstRun) {
          setTimeout(() => {
            this.tryInitialize();
          }, 3000);
        }
      });
  }

  private static _initialize(token: string): void {
    if (Socket.isConnected()) return;

    const WS_URL = `ws://${window.location.host}/ws?token=${token}`;
    Socket._socket = new WebSocket(WS_URL);

    Socket._socket.onopen = (e) => {
      toast.stickySuccess("ws", "Connected to server.");
      Socket.callbacks.open?.forEach((callback) => {
        callback(e);
      });
    };

    Socket._socket.onmessage = (e) => {
      handleAssistantMessage(e.data);
    };

    Socket._socket.onerror = () => {
      const msg = "Connection failed. Retry...";
      toast.stickyError("ws", msg);
    };

    Socket._socket.onclose = () => {
      // Reconnect after a delay
      setTimeout(() => {
        Socket.tryInitialize();
      }, 3000); // Reconnect after 3 seconds
    };

    this.isFirstRun = false;
  }

  static isConnected(): boolean {
    return (
      Socket._socket !== null && Socket._socket.readyState === WebSocket.OPEN
    );
  }

  static send(message: string): void {
    if (!Socket.isConnected()) Socket.tryInitialize();

    if (Socket.isConnected()) {
      Socket._socket?.send(message);
    } else {
      const msg = "Connection failed. Retry...";
      toast.stickyError("ws", msg);
    }
  }

  static addEventListener(
    event: string,
    callback: (e: MessageEvent) => void,
  ): void {
    Socket._socket?.addEventListener(
      event as keyof WebSocketEventMap,
      callback as (
        this: WebSocket,
        ev: WebSocketEventMap[keyof WebSocketEventMap],
      ) => never,
    );
  }

  static removeEventListener(
    event: string,
    listener: (e: Event) => void,
  ): void {
    Socket._socket?.removeEventListener(event, listener);
  }

  static registerCallback<K extends keyof WebSocketEventMap>(
    event: K,
    callbacks: ((data: WebSocketEventMap[K]) => void)[],
  ): void {
    if (Socket.callbacks[event] === undefined) {
      return;
    }
    Socket.callbacks[event].push(...callbacks);
  }
}

Socket.tryInitialize();

export default Socket;
