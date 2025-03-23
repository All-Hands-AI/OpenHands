import { useGetConfigQuery } from '../api/slices';

export const useConfig = () => {
  return useGetConfigQuery();
};