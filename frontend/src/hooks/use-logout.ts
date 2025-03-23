import { useLogoutMutation } from '../api/slices';

export const useLogout = () => {
  return useLogoutMutation();
};