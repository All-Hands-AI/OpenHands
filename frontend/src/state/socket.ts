import store from "../store";
import { setScreenshotSrc, setUrl } from "./browserSlice";

const MESSAGE_ACTIONS = ["terminal", "planner", "code", "browser"] as const;
type MessageAction = (typeof MESSAGE_ACTIONS)[number];

type SocketMessage = {
  action: MessageAction;
  data: Record<string, unknown>;
};

const messageActions = {
  browser: (message: SocketMessage) => {
    const { url, screenshotSrc } = message.data;
    store.dispatch(setUrl(url));
    store.dispatch(setScreenshotSrc(screenshotSrc));
  },
  terminal: () => {},
  planner: () => {},
  code: () => {},
};

const WS_URL = import.meta.env.VITE_TERMINAL_WS_URL;
if (!WS_URL) {
  throw new Error(
    "The environment variable VITE_TERMINAL_WS_URL is not set. Please set it to the WebSocket URL of the terminal server.",
  );
}

const socket = new WebSocket(WS_URL);

socket.addEventListener("message", (event) => {
  const { message } = JSON.parse(event.data);
  console.log("Received message:", message);

  if (message.action in messageActions) {
    const action = messageActions[message.action as MessageAction];
    action(message);
  }
});

export default socket;
