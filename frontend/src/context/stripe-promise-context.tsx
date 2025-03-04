import React from "react";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { useConfig } from "#/hooks/query/use-config";
import { loadStripe, Stripe } from "@stripe/stripe-js";

const StripePromiseContext = React.createContext<Promise<Stripe | null> | null>(null);

function StripePromiseProvider({ children }: React.PropsWithChildren) {
  const {data: config, isFetched, isLoading} = useConfig();
      const stripePromise = React.useMemo(() => {
          if (!isLoading && isFetched && config?.STRIPE_PUBLISHABLE_KEY) {
              return loadStripe(config.STRIPE_PUBLISHABLE_KEY);
          }
          return null;
      }, [isLoading, isFetched, config?.STRIPE_PUBLISHABLE_KEY])

  if (!stripePromise) {
    return (
    <div className="flex justify-center">
        <LoadingSpinner size="small" />
    </div>
    );
  }

  return <StripePromiseContext value={stripePromise}>{children}</StripePromiseContext>;
}

function useStripePromise() {
  const context = React.useContext(StripePromiseContext);
  if (context === undefined) {
    throw new Error("useStripe must be used within a StripeProvider");
  }
  return context;
}

export { StripePromiseProvider, useStripePromise };
