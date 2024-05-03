import { changeTaskState } from "#/state/agentSlice";
import { setScreenshotSrc, setUrl } from "#/state/browserSlice";
import { appendAssistantMessage } from "#/state/chatSlice";
import { setCode, updatePath } from "#/state/codeSlice";
import { appendInput } from "#/state/commandSlice";
import { appendJupyterInput } from "#/state/jupyterSlice";
import { setPlan } from "#/state/planSlice";
import { setInitialized } from "#/state/taskSlice";
import store from "#/store";
import ActionType from "#/types/ActionType";
import { ActionMessage } from "#/types/Message";
import { SocketMessage } from "#/types/ResponseType";
import { handleObservationMessage } from "./observations";
import { getPlan } from "./planService";

const messageActions = {
  [ActionType.INIT]: () => {
    store.dispatch(setInitialized(true));
  },
  [ActionType.RECONNECT]: () => {
    store.dispatch(setInitialized(true));
  },
  [ActionType.BROWSE]: (message: ActionMessage) => {
    const { url, screenshotSrc } = message.args;
    store.dispatch(setUrl(url));
    store.dispatch(setScreenshotSrc(screenshotSrc));
  },
  [ActionType.WRITE]: (message: ActionMessage) => {
    const { path, content } = message.args;
    store.dispatch(updatePath(path));
    store.dispatch(setCode(content));
  },
  [ActionType.THINK]: (message: ActionMessage) => {
    store.dispatch(appendAssistantMessage(message.args.thought));
  },
  [ActionType.TALK]: (message: ActionMessage) => {
    store.dispatch(appendAssistantMessage(message.args.content));
  },
  [ActionType.FINISH]: (message: ActionMessage) => {
    store.dispatch(appendAssistantMessage(message.message));
  },
  [ActionType.RUN]: (message: ActionMessage) => {
    if (message.args.thought) {
      store.dispatch(appendAssistantMessage(message.args.thought));
    }
    store.dispatch(appendInput(message.args.command));
  },
  [ActionType.RUN_IPYTHON]: (message: ActionMessage) => {
    if (message.args.thought) {
      store.dispatch(appendAssistantMessage(message.args.thought));
    }
    store.dispatch(appendJupyterInput(message.args.code));
  },
  [ActionType.ADD_TASK]: () => {
    getPlan().then((fetchedPlan) => store.dispatch(setPlan(fetchedPlan)));
  },
  [ActionType.MODIFY_TASK]: () => {
    getPlan().then((fetchedPlan) => store.dispatch(setPlan(fetchedPlan)));
  },
  [ActionType.CHANGE_TASK_STATE]: (message: ActionMessage) => {
    store.dispatch(changeTaskState(message.args.task_state));
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
