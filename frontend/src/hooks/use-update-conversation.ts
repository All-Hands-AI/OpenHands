import { useUpdateConversationMutation } from '../api/slices';

export const useUpdateConversation = () => {
  return useUpdateConversationMutation();
};