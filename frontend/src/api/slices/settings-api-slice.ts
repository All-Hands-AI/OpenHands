import { apiService } from '../api-service';
import { ApiSettings, PostApiSettings } from '../../types/settings';

export const settingsApiSlice = apiService.injectEndpoints({
  endpoints: (builder) => ({
    getSettings: builder.query<ApiSettings, void>({
      query: () => ({
        url: '/api/settings',
        method: 'GET',
      }),
      providesTags: ['Settings'],
    }),
    saveSettings: builder.mutation<boolean, Partial<PostApiSettings>>({
      query: (settings) => ({
        url: '/api/settings',
        method: 'POST',
        data: settings,
      }),
      transformResponse: (response, meta) => meta?.response?.status === 200,
      invalidatesTags: ['Settings'],
    }),
  }),
});

export const {
  useGetSettingsQuery,
  useSaveSettingsMutation,
} = settingsApiSlice;