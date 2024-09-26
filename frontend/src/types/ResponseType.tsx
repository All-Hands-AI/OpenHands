import { ActionMessage, ObservationMessage, StatusMessage } from "./Message";

type SocketMessage = ActionMessage | ObservationMessage | StatusMessage;

export { type SocketMessage };
