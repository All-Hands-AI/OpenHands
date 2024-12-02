import ActionType from "#/types/action-type";

export function createChatMessage(
  message: string,
  image_urls: string[],
  timestamp: string,
  secondary_id?: string,
) {
  const event = {
    action: ActionType.MESSAGE,
    args: { content: message, image_urls, timestamp, secondary_id },
  };
  return event;
}
