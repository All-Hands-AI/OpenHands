import store from "../store";
import { appendError, removeError } from "../state/errorsSlice";
import { handleAssistantMessage } from "./actions";
import { getToken } from "./auth";
import ActionType from "../types/ActionType";

class Socket {
  private static _socket: WebSocket | null = null;

  public static initialize(): void {
    getToken()
      .then((token) => {
        Socket._initialize(token);
      })
      .catch((err) => {
        const msg = `Failed to get token: ${err}.`;
        store.dispatch(appendError(msg));
        setTimeout(() => {
          store.dispatch(removeError(msg));
        }, 2000);
      });
  }

  private static _initialize(token: string): void {
    if (!Socket._socket || Socket._socket.readyState !== WebSocket.OPEN) {
      const WS_URL = `ws://${window.location.host}/ws?token=${token}`;
      Socket._socket = new WebSocket(WS_URL);

      Socket._socket.onopen = () => {
        const model = localStorage.getItem("model") || "gpt-3.5-turbo-1106";
        const agent = localStorage.getItem("agent") || "MonologueAgent";
        const workspaceDirectory =
          localStorage.getItem("workspaceDirectory") || "./workspace";
        Socket._socket?.send(
          JSON.stringify({
            action: ActionType.INIT,
            args: {
              model,
              agent_cls: agent,
              directory: workspaceDirectory,
            },
          }),
        );
      };

      Socket._socket.onmessage = (e) => {
        handleAssistantMessage(e.data);
      };

      Socket._socket.onerror = () => {
        const msg = "Failed connection to server";
        store.dispatch(appendError(msg));
        setTimeout(() => {
          store.dispatch(removeError(msg));
        }, 2000);
      };

      Socket._socket.onclose = () => {
        // Reconnect after a delay
        setTimeout(() => {
          Socket.initialize();
        }, 3000); // Reconnect after 3 seconds
      };
    }
  }

  static send(message: string): void {
    Socket.initialize();
    if (Socket._socket && Socket._socket.readyState === WebSocket.OPEN) {
      Socket._socket.send(message);
    } else {
      store.dispatch(appendError("WebSocket connection is not ready."));
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
}

Socket.initialize();

export default Socket;
