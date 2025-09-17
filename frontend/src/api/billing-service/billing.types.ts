export type SubscriptionAccess = {
  start_at: string;
  end_at: string;
  created_at: string;
  cancelled_at?: string | null;
  stripe_subscription_id?: string | null;
};

export interface CancelSubscriptionResponse {
  status: string;
  message: string;
}
