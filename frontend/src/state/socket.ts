import store from "../store";
import { setScreenshotSrc, setUrl } from "./browserSlice";
import { appendAssistantMessage } from "./chatSlice";
import { setCode } from "./codeSlice";
import { appendError } from "./errorsSlice";
import { setInitialized } from "./taskSlice";

const MESSAGE_ACTIONS = ["terminal", "planner", "code", "browser"] as const;
type MessageAction = (typeof MESSAGE_ACTIONS)[number];

type SocketMessage = {
  action: MessageAction;
  message: string;
  args: Record<string, unknown>;
};

const messageActions = {
  initialize: () => {
    store.dispatch(setInitialized(true));
    store.dispatch(
      appendAssistantMessage(
        "Hello, I am OpenDevin, an AI Software Engineer. What would you like me to build you today?",
      ),
    );
  },
  browse: (message: SocketMessage) => {
    const { url, screenshotSrc } = message.args;
    store.dispatch(setUrl(url));
    store.dispatch(setScreenshotSrc(screenshotSrc));
  },
  write: (message: SocketMessage) => {
    store.dispatch(setCode(message.args.contents));
  },
  think: (message: SocketMessage) => {
    store.dispatch(appendAssistantMessage(message.args.thought));
  },
  finish: (message: SocketMessage) => {
    store.dispatch(appendAssistantMessage(message.message));
  },
};

const WS_URL = import.meta.env.VITE_TERMINAL_WS_URL;
if (!WS_URL) {
  throw new Error(
    "The environment variable VITE_TERMINAL_WS_URL is not set. Please set it to the WebSocket URL of the terminal server.",
  );
}

const socket = new WebSocket(WS_URL);

socket.addEventListener("message", (event) => {
  const socketMessage = JSON.parse(event.data) as SocketMessage;

  if (socketMessage.action in messageActions) {
    const actionFn =
      messageActions[socketMessage.action as keyof typeof messageActions];
    actionFn(socketMessage);
  } else if (!socketMessage.action) {
    store.dispatch(appendAssistantMessage(socketMessage.message));
  }
});
socket.addEventListener("error", () => {
  store.dispatch(
    appendError(
      `Failed connection to server. Please ensure the server is reachable at ${WS_URL}.`,
    ),
  );
});

export default socket;
