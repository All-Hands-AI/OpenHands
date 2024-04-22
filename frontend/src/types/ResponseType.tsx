import { ActionMessage, ObservationMessage } from "./Message";

type Role = "user" | "assistant";

interface ResConfigurations {
  [key: string]: string | boolean | number;
}

interface ResFetchToken {
  token: string;
}

interface ResFetchMsgTotal {
  msg_total: number;
}

interface ResFetchMsg {
  id: string;
  role: Role;
  payload: SocketMessage;
}

interface ResFetchMsgs {
  messages: ResFetchMsg[];
}

interface ResDelMsg {
  ok: string;
}

type SocketMessage = ActionMessage | ObservationMessage;

export {
  type ResConfigurations,
  type ResFetchToken,
  type ResFetchMsgTotal,
  type ResFetchMsg,
  type ResFetchMsgs,
  type ResDelMsg,
  type SocketMessage,
};
