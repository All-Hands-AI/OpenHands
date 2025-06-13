import {
  AssistantMessageAction,
  UserMessageAction,
} from "#/types/core/actions";
import i18n from "#/i18n";
import { isUserMessage } from "#/types/core/guards";

export const parseMessageFromEvent = (
  event: UserMessageAction | AssistantMessageAction,
): string => {
  const m = isUserMessage(event) ? event.args.content : event.message;
  if (!event.args.file_urls || event.args.file_urls.length === 0) {
    return m;
  }
  const delimiter = i18n.t("CHAT_INTERFACE$AUGMENTED_PROMPT_FILES_TITLE");
  const parts = m.split(delimiter);

  return parts[0];
};
