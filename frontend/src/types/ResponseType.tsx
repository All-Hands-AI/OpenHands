import { ActionMessage, ObservationMessage } from "./Message";

interface ResFetchToken {
  token: string;
}

interface ResFetchMsgTotal {
  msg_total: number;
}

interface ResFetchMsg {
  id: string;
  role: string;
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
  type ResFetchToken,
  type ResFetchMsgTotal,
  type ResFetchMsg,
  type ResFetchMsgs,
  type ResDelMsg,
  type SocketMessage,
};
