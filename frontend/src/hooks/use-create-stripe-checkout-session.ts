import { useCreateCheckoutSessionMutation } from "../api/slices";

export const useCreateStripeCheckoutSession = () =>
  useCreateCheckoutSessionMutation();
