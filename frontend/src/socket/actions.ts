import store from "../store";
import { ActionMessage } from "./types/Message";
import { setScreenshotSrc, setUrl } from "../state/browserSlice";
import { appendAssistantMessage } from "../state/chatSlice";
import { setCode } from "../state/codeSlice";
import { setInitialized } from "../state/taskSlice";

const messageActions = {
  initialize: () => {
    store.dispatch(setInitialized(true));
    store.dispatch(
      appendAssistantMessage(
        "Hello, I am OpenDevin, an AI Software Engineer. What would you like me to build you today?",
      ),
    );
  },
  browse: (message: ActionMessage) => {
    const { url, screenshotSrc } = message.args;
    store.dispatch(setUrl(url));
    store.dispatch(setScreenshotSrc(screenshotSrc));
  },
  write: (message: ActionMessage) => {
    store.dispatch(setCode(message.args.contents));
  },
  think: (message: ActionMessage) => {
    store.dispatch(appendAssistantMessage(message.args.thought));
  },
  finish: (message: ActionMessage) => {
    store.dispatch(appendAssistantMessage(message.message));
  },
};

export function handleActionMessage(message: ActionMessage) {
  if (message.action in messageActions) {
    const actionFn =
      messageActions[message.action as keyof typeof messageActions];
    actionFn(message);
  }
}
