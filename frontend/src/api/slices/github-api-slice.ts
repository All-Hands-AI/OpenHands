import { apiService } from '../api-service';

interface SearchRepositoriesParams {
  query: string;
  per_page?: number;
}

export const githubApiSlice = apiService.injectEndpoints({
  endpoints: (builder) => ({
    getGitHubUser: builder.query<GitHubUser, void>({
      query: () => ({
        url: '/api/github/user',
        method: 'GET',
      }),
      transformResponse: (data: GitHubUser) => ({
        id: data.id,
        login: data.login,
        avatar_url: data.avatar_url,
        company: data.company,
        name: data.name,
        email: data.email,
      }),
      providesTags: ['User'],
    }),
    getGitHubUserInstallationIds: builder.query<number[], void>({
      query: () => ({
        url: '/api/github/installations',
        method: 'GET',
      }),
      providesTags: ['Installations'],
    }),
    searchGitHubRepositories: builder.query<GitHubRepository[], SearchRepositoriesParams>({
      query: ({ query, per_page = 5 }) => ({
        url: '/api/github/search/repositories',
        method: 'GET',
        params: {
          query,
          per_page,
        },
      }),
      providesTags: ['Repositories'],
    }),
  }),
});

export const {
  useGetGitHubUserQuery,
  useGetGitHubUserInstallationIdsQuery,
  useSearchGitHubRepositoriesQuery,
} = githubApiSlice;