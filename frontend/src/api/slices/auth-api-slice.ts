import { apiService } from '../api-service';
import { 
  AuthenticateResponse, 
  GitHubAccessTokenResponse,
  Conversation,
  ResultSet,
  Feedback,
  FeedbackResponse
} from '../open-hands.types';
import { GetConfigResponse } from '../open-hands.types';

interface AuthenticateParams {
  appMode: GetConfigResponse['APP_MODE'];
}

interface SubmitFeedbackParams {
  conversationId: string;
  feedback: Feedback;
}

interface UpdateConversationParams {
  conversationId: string;
  conversation: Partial<Omit<Conversation, 'conversation_id'>>;
}

interface CreateConversationParams {
  selectedRepository?: string;
  initialUserMsg?: string;
  imageUrls?: string[];
}

export const authApiSlice = apiService.injectEndpoints({
  endpoints: (builder) => ({
    authenticate: builder.mutation<boolean, AuthenticateParams>({
      query: ({ appMode }) => ({
        url: '/api/authenticate',
        method: 'POST',
      }),
      transformResponse: (response: AuthenticateResponse, meta) => meta?.response?.status === 200,
    }),
    getGitHubAccessToken: builder.mutation<GitHubAccessTokenResponse, string>({
      query: (code) => ({
        url: '/api/keycloak/callback',
        method: 'POST',
        data: { code },
      }),
    }),
    getUserConversations: builder.query<Conversation[], void>({
      query: () => ({
        url: '/api/conversations?limit=9',
        method: 'GET',
      }),
      transformResponse: (response: ResultSet<Conversation>) => response.results,
      providesTags: ['Conversations'],
    }),
    getUserConversation: builder.query<Conversation | null, string>({
      query: (conversationId) => ({
        url: `/api/conversations/${conversationId}`,
        method: 'GET',
      }),
      providesTags: (result, error, conversationId) => [
        { type: 'Conversation', id: conversationId },
      ],
    }),
    createConversation: builder.mutation<Conversation, CreateConversationParams>({
      query: ({ selectedRepository, initialUserMsg, imageUrls }) => ({
        url: '/api/conversations',
        method: 'POST',
        data: {
          selected_repository: selectedRepository,
          selected_branch: undefined,
          initial_user_msg: initialUserMsg,
          image_urls: imageUrls,
        },
      }),
      invalidatesTags: ['Conversations'],
    }),
    updateConversation: builder.mutation<void, UpdateConversationParams>({
      query: ({ conversationId, conversation }) => ({
        url: `/api/conversations/${conversationId}`,
        method: 'PATCH',
        data: conversation,
      }),
      invalidatesTags: (result, error, { conversationId }) => [
        { type: 'Conversation', id: conversationId },
        'Conversations',
      ],
    }),
    deleteConversation: builder.mutation<void, string>({
      query: (conversationId) => ({
        url: `/api/conversations/${conversationId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Conversations'],
    }),
    submitFeedback: builder.mutation<FeedbackResponse, SubmitFeedbackParams>({
      query: ({ conversationId, feedback }) => ({
        url: `/api/conversations/${conversationId}/submit-feedback`,
        method: 'POST',
        data: feedback,
      }),
    }),
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/api/logout',
        method: 'POST',
      }),
    }),
  }),
});

export const {
  useAuthenticateMutation,
  useGetGitHubAccessTokenMutation,
  useGetUserConversationsQuery,
  useGetUserConversationQuery,
  useCreateConversationMutation,
  useUpdateConversationMutation,
  useDeleteConversationMutation,
  useSubmitFeedbackMutation,
  useLogoutMutation,
} = authApiSlice;