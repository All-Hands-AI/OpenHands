import { useGetVSCodeUrlQuery } from '../api/slices';
import { useConversation } from '../context/conversation-context';

export const useVSCodeUrl = () => {
  const { conversationId } = useConversation();
  return useGetVSCodeUrlQuery(conversationId);
};