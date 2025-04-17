/**
 * Returns a URL compatible for the file service
 * @param conversationId ID of the conversation
 * @returns URL of the conversation
 */
export const getConversationUrl = (conversationId: string) =>
  `/api/conversations/${conversationId}`;
