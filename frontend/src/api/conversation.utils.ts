import ConversationService from "#/api/conversation-service/conversation-service.api";

/**
 * Returns a URL compatible for the file service
 * @param conversationId ID of the conversation
 * @returns URL of the conversation
 */
export const getConversationUrl = (conversationId: string) =>
  ConversationService.getConversationUrl(conversationId);
