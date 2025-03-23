import { useGetUserConversationsQuery } from '../api/slices';

export const useUserConversations = () => {
  return useGetUserConversationsQuery();
};