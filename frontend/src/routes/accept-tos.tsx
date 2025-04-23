import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router";
import { I18nKey } from "#/i18n/declaration";
import AllHandsLogo from "#/assets/branding/all-hands-logo.svg?react";
import { TOSCheckbox } from "#/components/features/waitlist/tos-checkbox";
import { BrandButton } from "#/components/features/settings/brand-button";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";

export default function AcceptTOS() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isTosAccepted, setIsTosAccepted] = React.useState(false);

  // Get the return URL from the query parameters
  const returnUrl = searchParams.get("returnUrl") || "/";

  const handleAcceptTOS = () => {
    if (isTosAccepted) {
      // Set consent for analytics
      handleCaptureConsent(true);

      // Store TOS acceptance in localStorage to remember it
      localStorage.setItem("tosAccepted", "true");

      // Check if the return URL is an external URL (starts with http or https)
      if (returnUrl.startsWith("http://") || returnUrl.startsWith("https://")) {
        // For external URLs, redirect using window.location
        window.location.href = returnUrl;
      } else {
        // For internal routes, use navigate
        navigate(returnUrl);
      }
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="border border-tertiary p-8 rounded-lg max-w-md w-full flex flex-col gap-6 items-center">
        <AllHandsLogo width={68} height={46} />

        <div className="flex flex-col gap-2 w-full items-center text-center">
          <h1 className="text-2xl font-bold">
            {t(I18nKey.TOS$ACCEPT_TERMS_OF_SERVICE)}
          </h1>
          <p className="text-sm text-gray-500">
            {t(I18nKey.TOS$ACCEPT_TERMS_DESCRIPTION)}
          </p>
        </div>

        <TOSCheckbox onChange={() => setIsTosAccepted((prev) => !prev)} />

        <BrandButton
          isDisabled={!isTosAccepted}
          type="button"
          variant="primary"
          onClick={handleAcceptTOS}
          className="w-full"
        >
          {t(I18nKey.TOS$CONTINUE)}
        </BrandButton>
      </div>
    </div>
  );
}
