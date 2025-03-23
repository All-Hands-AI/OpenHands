import { useCreateCheckoutSessionMutation } from '../api/slices';

export const useCreateStripeCheckoutSession = () => {
  return useCreateCheckoutSessionMutation();
};