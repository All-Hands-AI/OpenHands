import store from "../store";
import { ActionMessage } from "../types/Message";
import { setScreenshotSrc, setUrl } from "../state/browserSlice";
import { appendAssistantMessage } from "../state/chatSlice";
import { setCode } from "../state/codeSlice";
import { setInitialized } from "../state/taskSlice";
import { handleObservationMessage } from "./observations";
import { appendInput } from "../state/commandSlice";
import { SocketMessage } from "../types/ResponseType";

let isInitialized = false;

const messageActions = {
  initialize: () => {
    store.dispatch(setInitialized(true));
    if (isInitialized) {
      return;
    }
    store.dispatch(
      appendAssistantMessage(
        "Hi! I'm OpenDevin, an AI Software Engineer. What would you like to build with me today?",
      ),
    );
    isInitialized = true;
  },
  browse: (message: ActionMessage) => {
    const { url, screenshotSrc } = message.args;
    store.dispatch(setUrl(url));
    store.dispatch(setScreenshotSrc(screenshotSrc));
  },
  write: (message: ActionMessage) => {
    store.dispatch(setCode(message.args.content));
  },
  think: (message: ActionMessage) => {
    store.dispatch(appendAssistantMessage(message.args.thought));
  },
  finish: (message: ActionMessage) => {
    store.dispatch(appendAssistantMessage(message.message));
  },
  run: (message: ActionMessage) => {
    store.dispatch(appendInput(message.args.command));
  },
};

export function handleActionMessage(message: ActionMessage) {
  if (message.action in messageActions) {
    const actionFn =
      messageActions[message.action as keyof typeof messageActions];
    actionFn(message);
  }
}

export function handleAssistantMessage(data: string | SocketMessage) {
  let socketMessage: SocketMessage;

  if (typeof data === "string") {
    socketMessage = JSON.parse(data) as SocketMessage;
  } else {
    socketMessage = data;
  }

  if ("action" in socketMessage) {
    handleActionMessage(socketMessage);
  } else {
    handleObservationMessage(socketMessage);
  }
}
