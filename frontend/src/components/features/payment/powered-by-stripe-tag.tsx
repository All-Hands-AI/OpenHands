import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import stripeLogo from "#/assets/stripe.svg";

export function PoweredByStripeTag() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-row items-center">
      <span className="text-medium font-semi-bold">
        {t(I18nKey.BILLING$POWERED_BY)}
      </span>
      <img src={stripeLogo} alt="Stripe" className="h-8" />
    </div>
  );
}
