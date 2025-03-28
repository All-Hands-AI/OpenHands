/**
 * Returns a URL compatible for the file service
 * @param conversationId ID of the conversation
 * @returns URL of the conversation endpoint
 * @example
 * getConversationUrl("123"); // "/api/conversations/123"
 * getConversationUrl(); // "/api/conversations"
 */
export const getConversationUrl = (conversationId?: string) => {
  const url = "/api/conversations";
  return conversationId ? `${url}/${conversationId}` : url;
};
