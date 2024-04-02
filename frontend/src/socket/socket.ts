import store from "../store";
import { ActionMessage, ObservationMessage } from "../types/Message";
import { appendError } from "../state/errorsSlice";
import { handleActionMessage } from "./actions";
import { handleObservationMessage } from "./observations";

type SocketMessage = ActionMessage | ObservationMessage;

const WS_URL = `ws://${window.location.host}/ws`;

const socket = new WebSocket(WS_URL);

socket.addEventListener("message", (event) => {
  const socketMessage = JSON.parse(event.data) as SocketMessage;
  if ("action" in socketMessage) {
    handleActionMessage(socketMessage);
  } else if ("observation" in socketMessage) {
    handleObservationMessage(socketMessage);
  } else {
    /* 
      TODO
      This condition fires for user messages when terminal input is
      entered.  Terminal input will be specified with the 
      message type "term": "output", possibly handle
    */
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
