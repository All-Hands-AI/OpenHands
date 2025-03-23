import { useGetGitHubUserQuery } from '../api/slices';

export const useGithubUser = () => {
  return useGetGitHubUserQuery();
};