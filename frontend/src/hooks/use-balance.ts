import { useGetBalanceQuery } from '../api/slices';

export const useBalance = () => {
  return useGetBalanceQuery();
};