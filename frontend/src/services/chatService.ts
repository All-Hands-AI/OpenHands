import ActionType from "#/types/ActionType";

export function createChatMessage(message: string, images_urls: string[]) {
  const event = {
    action: ActionType.MESSAGE,
    args: { content: message, images_urls },
  };
  return JSON.stringify(event);
}
