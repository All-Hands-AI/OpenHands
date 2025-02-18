import { redirect, useSearchParams } from "react-router";
import React from "react";
import { PaymentForm } from "#/components/features/payment/payment-form";
import { GetConfigResponse } from "#/api/open-hands.types";
import { queryClient } from "#/entry.client";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { BILLING_SETTINGS } from "#/utils/feature-flags";

export const clientLoader = async () => {
  const config = queryClient.getQueryData<GetConfigResponse>(["config"]);

  if (config?.APP_MODE !== "saas" || !BILLING_SETTINGS()) {
    return redirect("/settings");
  }

  return null;
};

function BillingSettingsScreen() {
  const [searchParams, setSearchParams] = useSearchParams();
  const checkoutStatus = searchParams.get("checkout");

  React.useEffect(() => {
    if (checkoutStatus === "success") {
      displaySuccessToast("Payment successful");
    } else if (checkoutStatus === "cancel") {
      displayErrorToast("Payment cancelled");
    }

    setSearchParams({});
  }, [checkoutStatus]);

  return <PaymentForm />;
}

export default BillingSettingsScreen;
