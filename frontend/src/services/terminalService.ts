import ActionType from "#/types/ActionType";
import Session from "./session";

export function sendTerminalCommand(command: string): void {
  const event = { action: ActionType.RUN, args: { command } };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}

export function subscribeToTerminalOutput(
  callback: (output: string) => void,
): () => void {
  const handleMessage = (event: Event) => {
    if (event instanceof MessageEvent) {
      const data = JSON.parse(event.data);
      if (data.action === ActionType.TERMINAL_OUTPUT) {
        callback(data.output);
      }
    }
  };

  Session.addEventListener("message", handleMessage);

  return () => {
    Session.removeEventListener("message", handleMessage);
  };
}
