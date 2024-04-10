import {
  ResDelMsg,
  ResFetchMsgs,
  ResFetchMsgTotal,
} from "../types/ResponseType";

const fetchMsgTotal = async (): Promise<ResFetchMsgTotal> => {
  const headers = new Headers({
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });
  const response = await fetch(`/api/messages/total`, { headers });
  if (response.status !== 200) {
    throw new Error("Get message total failed.");
  }
  const data: ResFetchMsgTotal = await response.json();
  return data;
};

const fetchMsgs = async (): Promise<ResFetchMsgs> => {
  const headers = new Headers({
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });
  const response = await fetch(`/api/messages`, { headers });
  if (response.status !== 200) {
    throw new Error("Get messages failed.");
  }
  const data: ResFetchMsgs = await response.json();
  return data;
};

const clearMsgs = async (): Promise<ResDelMsg> => {
  const headers = new Headers({
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("token")}`,
  });
  const response = await fetch(`/api/messages`, {
    method: "DELETE",
    headers,
  });
  if (response.status !== 200) {
    throw new Error("Delete messages failed.");
  }
  const data: ResDelMsg = await response.json();
  return data;
};

export { fetchMsgTotal, fetchMsgs, clearMsgs };
