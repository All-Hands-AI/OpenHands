import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router";
import { openHands } from "#/api/open-hands-axios";

function BillingRedirect() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id")?.toString();

  const { data, isLoading } = useQuery({
    queryKey: ["checkout-session", sessionId],
    queryFn: async () => {
      const response = await openHands.get<{
        status: "complete" | "open";
        customer_email: string | undefined;
      }>("/api/session-status", {
        params: { session_id: sessionId },
      });

      return response.data;
    },
  });

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
