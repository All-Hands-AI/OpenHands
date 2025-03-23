import { useCreateConversationMutation } from '../api/slices';

export const useCreateConversation = () => {
  return useCreateConversationMutation();
};