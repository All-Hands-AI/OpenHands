import ActionType from "#/types/ActionType";
import Session from "./session";

export function updateBrowserTabUrl(newUrl: string): void {
  const event = { action: ActionType.BROWSE, args: { url: newUrl } };
  const eventString = JSON.stringify(event);
  Session.send(eventString);
}
