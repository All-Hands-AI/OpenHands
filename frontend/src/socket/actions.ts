import { setScreenshotSrc, setUrl } from "../state/browserSlice";
import { appendAssistantMessage } from "../state/chatSlice";
import { setCode, updatePath } from "../state/codeSlice";
import { setInitialized } from "../state/taskSlice";
import store from "../store";
import { ActionMessage } from "../types/Message";

const messageActions = {
  initialize: () => {
    store.dispatch(setInitialized(true));
    store.dispatch(
      appendAssistantMessage(
        "Hi! I'm OpenDevin, an AI Software Engineer. What would you like to build with me today?",
      ),
    );
  },
  browse: (message: ActionMessage) => {
    const { url, screenshotSrc } = message.args;
    store.dispatch(setUrl(url));
    store.dispatch(setScreenshotSrc(screenshotSrc));
  },
  write: (message: ActionMessage) => {
    const { path, content } = message.args;
    store.dispatch(updatePath(path));
    store.dispatch(setCode(content));
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
