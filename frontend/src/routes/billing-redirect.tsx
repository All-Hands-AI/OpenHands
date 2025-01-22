import { useNavigate, useSearchParams } from "react-router";
import React from "react";
import { useCheckStripePaymentStatus } from "#/hooks/query/stripe/use-check-stripe-payment-status";

function BillingRedirect() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const sessionId = searchParams.get("session_id")?.toString();

  const { data, isLoading } = useCheckStripePaymentStatus(sessionId);

  React.useEffect(() => {
    if (data?.status === "complete") {
      navigate("/");
    }
  }, [data?.status]);

  return (
    <div>
      {isLoading && <h1>Verifying...</h1>}
      {data?.status === "complete" && (
        <h1>Payment complete for {data.customer_email || "you"}</h1>
      )}
      {data?.status === "open" && <h1>Payment failed</h1>}
    </div>
  );
}

export default BillingRedirect;
