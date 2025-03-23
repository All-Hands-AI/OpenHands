import { apiService } from '../api-service';

export const billingApiSlice = apiService.injectEndpoints({
  endpoints: (builder) => ({
    getBalance: builder.query<string, void>({
      query: () => ({
        url: '/api/billing/credits',
        method: 'GET',
      }),
      transformResponse: (response: { credits: string }) => response.credits,
      providesTags: ['Balance'],
    }),
    createCheckoutSession: builder.mutation<string, number>({
      query: (amount) => ({
        url: '/api/billing/create-checkout-session',
        method: 'POST',
        data: { amount },
      }),
      transformResponse: (response: { redirect_url: string }) => response.redirect_url,
    }),
    createBillingSessionResponse: builder.mutation<string, void>({
      query: () => ({
        url: '/api/billing/create-customer-setup-session',
        method: 'POST',
      }),
      transformResponse: (response: { redirect_url: string }) => response.redirect_url,
    }),
  }),
});

export const {
  useGetBalanceQuery,
  useCreateCheckoutSessionMutation,
  useCreateBillingSessionResponseMutation,
} = billingApiSlice;