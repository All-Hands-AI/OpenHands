import { changeTaskState } from "src/state/agentSlice";
import { setScreenshotSrc, setUrl } from "src/state/browserSlice";
import { appendAssistantMessage } from "src/state/chatSlice";
import { setCode, updatePath } from "src/state/codeSlice";
import { appendInput } from "src/state/commandSlice";
import { setPlan } from "src/state/planSlice";
import { setInitialized } from "src/state/taskSlice";
import store from "src/store";
import ActionType from "src/types/ActionType";
import { ActionMessage } from "src/types/Message";
import { SocketMessage } from "src/types/ResponseType";
import { handleObservationMessage } from "./observations";
import { getPlan } from "./planService";

const messageActions = {
  [ActionType.INIT]: () => {
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
  [ActionType.FINISH]: (message: ActionMessage) => {
    store.dispatch(appendAssistantMessage(message.message));
  },
  [ActionType.RUN]: (message: ActionMessage) => {
    store.dispatch(appendInput(message.args.command));
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
