import i18n from "#/i18n";
import { MessageEvent } from "#/types/v1/core";

export const parseMessageFromEvent = (event: MessageEvent): string => {
  if (event.llm_message.content[0].type === "text") {
    return event.llm_message.content[0].text;
  }
  if (event.llm_message.content[0].type === "image") {
    return i18n.t("CHAT_INTERFACE$AUGMENTED_PROMPT_FILES_TITLE");
  }

  return "";
};
