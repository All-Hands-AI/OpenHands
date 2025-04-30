import { useSearchParams } from "react-router";
import React from "react";
import { useTranslation } from "react-i18next";
import { PaymentForm } from "#/components/features/payment/payment-form";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { I18nKey } from "#/i18n/declaration";

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
