import socket from "../socket/socket";

export function sendSelectedMessage(file: string): void {
  const event = { action: "file_selected", args: { file } };
  const eventString = JSON.stringify(event);
  socket.send(eventString);
}

export function sendRefreshFilesMessage(): void {
  const event = { action: "refresh_files" };
  const eventString = JSON.stringify(event);
  socket.send(eventString);
}
