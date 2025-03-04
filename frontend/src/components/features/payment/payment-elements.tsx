import { PropsWithChildren, useMemo } from "react";
import { Elements } from "@stripe/react-stripe-js";
import { loadStripe } from "@stripe/stripe-js";
import { useConfig } from "#/hooks/query/use-config";
import { LoadingSpinner } from "#/components/shared/loading-spinner";

export const PaymentElements = ({ children }: PropsWithChildren) => {
    const {data: config, isFetched, isLoading} = useConfig();
    const stripePromise = useMemo(() => {
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
    return (
        <Elements
          stripe={stripePromise}
          options={{
            mode: "setup",
            currency: "usd",
            appearance: {
              theme: "night",
              variables: {
                colorPrimary: "#C9B974",
                iconColor: "#C9B974",
              },
            },
          }}
        >
          {children}
        </Elements>
    );
};
