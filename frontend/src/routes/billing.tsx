import { redirect, useSearchParams } from "react-router";
import React from "react";
import { useTranslation } from "react-i18next";
import { PaymentForm } from "#/components/features/payment/payment-form";
import { GetConfigResponse } from "#/api/open-hands.types";
import { queryClient } from "#/entry.client";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { I18nKey } from "#/i18n/declaration";

export const clientLoader = async () => {
  const config = queryClient.getQueryData<GetConfigResponse>(["config"]);

  if (config?.APP_MODE !== "saas" || !config.FEATURE_FLAGS.ENABLE_BILLING) {
    return redirect("/settings");
  }

  return null;
};

function BillingSettingsScreen() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const checkoutStatus = searchParams.get("checkout");

  React.useEffect(() => {
    if (checkoutStatus === "success") {
      displaySuccessToast(t(I18nKey.PAYMENT$SUCCESS));
    } else if (checkoutStatus === "cancel") {
      displayErrorToast(t(I18nKey.PAYMENT$CANCELLED));
    }

    setSearchParams({});
  }, [checkoutStatus]);

  return <PaymentForm />;
}

export default BillingSettingsScreen;
