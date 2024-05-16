import { setScreenshotSrc, setUrl } from "#/state/browserSlice";
import { addAssistantMessage } from "#/state/chatSlice";
import { setCode, updatePath } from "#/state/codeSlice";
import { appendInput } from "#/state/commandSlice";
import { appendJupyterInput } from "#/state/jupyterSlice";
import { setRootTask } from "#/state/taskSlice";
import store from "#/store";
import ActionType from "#/types/ActionType";
import { ActionMessage } from "#/types/Message";
import { SocketMessage } from "#/types/ResponseType";
import { handleObservationMessage } from "./observations";
import { getRootTask } from "./taskService";

const messageActions = {
  [ActionType.BROWSE]: (message: ActionMessage) => {
    const { url, screenshotSrc } = message.args;
    store.dispatch(setUrl(url));
    store.dispatch(setScreenshotSrc(screenshotSrc));
  },
  [ActionType.BROWSE_INTERACTIVE]: (message: ActionMessage) => {
    const { url, screenshotSrc } = message.args;
    store.dispatch(setUrl(url));
    store.dispatch(setScreenshotSrc(screenshotSrc));
  },
  [ActionType.WRITE]: (message: ActionMessage) => {
    const { path, content } = message.args;
    store.dispatch(updatePath(path));
    store.dispatch(setCode(content));
  },
  [ActionType.MESSAGE]: (message: ActionMessage) => {
    store.dispatch(addAssistantMessage(message.args.content));
  },
  [ActionType.FINISH]: (message: ActionMessage) => {
    store.dispatch(addAssistantMessage(message.message));
  },
  [ActionType.RUN]: (message: ActionMessage) => {
    if (message.args.thought) {
      store.dispatch(addAssistantMessage(message.args.thought));
    }
    store.dispatch(appendInput(message.args.command));
  },
  [ActionType.RUN_IPYTHON]: (message: ActionMessage) => {
    if (message.args.thought) {
      store.dispatch(addAssistantMessage(message.args.thought));
    }
    store.dispatch(appendJupyterInput(message.args.code));
  },
  [ActionType.ADD_TASK]: () => {
    getRootTask().then((fetchedRootTask) =>
      store.dispatch(setRootTask(fetchedRootTask)),
    );
  },
  [ActionType.MODIFY_TASK]: () => {
    getRootTask().then((fetchedRootTask) =>
      store.dispatch(setRootTask(fetchedRootTask)),
    );
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
