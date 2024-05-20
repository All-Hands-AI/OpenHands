// import { toast } from "sonner";
import toast from "#/utils/toast";
import { handleAssistantMessage } from "./actions";
import { getToken, setToken, clearToken } from "./auth";

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

  private static initializing = false;

  public static tryInitialize(): void {
    if (Socket.initializing) return;
    Socket.initializing = true;
    const token = getToken();
    Socket._initialize(token);
  }

  private static _initialize(token: string): void {
    if (Socket.isConnected()) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const WS_URL = `${protocol}//${window.location.host}/ws?token=${token}`;
    Socket._socket = new WebSocket(WS_URL);

    Socket._socket.onopen = (e) => {
      toast.success("ws", "Connected to server.");
      Socket.initializing = false;
      Socket.callbacks.open?.forEach((callback) => {
        callback(e);
      });
    };

    Socket._socket.onmessage = (e) => {
      let data = null;
      try {
        data = JSON.parse(e.data);
      } catch (err) {
        // TODO: report the error
        console.error("Error parsing JSON data", err);
        return;
      }
      if (data.error && data.error_code === 401) {
        clearToken();
      } else if (data.token) {
        setToken(data.token);
      } else {
        handleAssistantMessage(data);
      }
    };

    Socket._socket.onerror = () => {
      const msg = "Connection failed. Retry...";
      toast.error("ws", msg);
    };

    Socket._socket.onclose = () => {
      // Reconnect after a delay
      setTimeout(() => {
        Socket.tryInitialize();
      }, 3000); // Reconnect after 3 seconds
    };
  }

  static isConnected(): boolean {
    return (
      Socket._socket !== null && Socket._socket.readyState === WebSocket.OPEN
    );
  }

  static send(message: string): void {
    if (!Socket.isConnected()) {
      Socket.tryInitialize();
    }
    if (Socket.initializing) {
      setTimeout(() => Socket.send(message), 1000);
      return;
    }

    if (Socket.isConnected()) {
      Socket._socket?.send(message);
    } else {
      const msg = "Connection failed. Retry...";
      toast.error("ws", msg);
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

export default Socket;
