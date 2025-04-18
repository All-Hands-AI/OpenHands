import { ActionMessage, ObservationMessage, StatusMessage } from "./message";

type SocketMessage = ActionMessage | ObservationMessage | StatusMessage;

export { type SocketMessage };
