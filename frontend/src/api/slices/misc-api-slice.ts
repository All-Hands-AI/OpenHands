import { apiService } from '../api-service';
import { GetVSCodeUrlResponse, GetTrajectoryResponse } from '../open-hands.types';

export const miscApiSlice = apiService.injectEndpoints({
  endpoints: (builder) => ({
    getVSCodeUrl: builder.query<GetVSCodeUrlResponse, string>({
      query: (conversationId) => ({
        url: `/api/conversations/${conversationId}/vscode-url`,
        method: 'GET',
      }),
      providesTags: (result, error, conversationId) => [
        { type: 'VSCodeUrl', id: conversationId },
      ],
    }),
    getRuntimeId: builder.query<{ runtime_id: string }, string>({
      query: (conversationId) => ({
        url: `/api/conversations/${conversationId}/config`,
        method: 'GET',
      }),
    }),
    getTrajectory: builder.query<GetTrajectoryResponse, string>({
      query: (conversationId) => ({
        url: `/api/conversations/${conversationId}/trajectory`,
        method: 'GET',
      }),
    }),
  }),
});

export const {
  useGetVSCodeUrlQuery,
  useGetRuntimeIdQuery,
  useGetTrajectoryQuery,
} = miscApiSlice;