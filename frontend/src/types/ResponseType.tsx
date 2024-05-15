import { ActionMessage, ObservationMessage } from "./Message";

type Role = "user" | "assistant";

type SocketMessage = ActionMessage | ObservationMessage;

export {
  type SocketMessage,
};
