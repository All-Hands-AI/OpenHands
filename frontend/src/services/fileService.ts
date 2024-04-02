import socket from "../socket/socket";

export function getFiles() {
  const event = { action: "files" };
  const eventString = JSON.stringify(event);
  socket.send(eventString);
}
