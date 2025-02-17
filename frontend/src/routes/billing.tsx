import { redirect } from "react-router";
import { PaymentForm } from "#/components/features/payment/payment-form";
import { GetConfigResponse } from "#/api/open-hands.types";
import { queryClient } from "#/entry.client";

export const clientLoader = async () => {
  const config = queryClient.getQueryData<GetConfigResponse>(["config"]);

  if (config?.APP_MODE !== "saas") {
    return redirect("/settings");
  }

  return null;
};

function BillingSettingsScreen() {
  return <PaymentForm />;
}

export default BillingSettingsScreen;
