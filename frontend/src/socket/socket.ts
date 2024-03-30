import store from "../store";
import { ActionMessage, ObservationMessage } from "./types/Message";
import { appendError } from "../state/errorsSlice";
import { handleActionMessage } from "./actions";
import { handleObservationMessage } from "./observations";

type SocketMessage = ActionMessage | ObservationMessage;

const WS_URL = import.meta.env.VITE_WS_URL;
if (!WS_URL) {
  throw new Error(
    "The environment variable VITE_WS_URL is not set. Please set it to the WebSocket URL of the terminal server.",
  );
}

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
      This now enters for user messages when terminal input is
      entered.  Terminal input will be specified with the 
      message type "term": "output"
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
