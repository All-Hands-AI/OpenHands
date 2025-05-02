import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearchParams } from "react-router";
import OpenHands from "#/api/open-hands";
import { useAuth } from "#/context/auth-context";
import { I18nKey } from "#/i18n/declaration";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setProvidersAreSet } = useAuth();
  const { t } = useTranslation();
  const [isProcessing, setIsProcessing] = React.useState(true);

  React.useEffect(() => {
    const code = searchParams.get("code");

    if (!code) {
      displayErrorToast(t(I18nKey.AUTH$AUTHENTICATION_FAILED));
      navigate("/");
      return;
    }

    const processOAuthCallback = async () => {
      try {
        // Process the OAuth callback
        await OpenHands.getGitHubAccessToken(code);

        // Set authentication state
        setProvidersAreSet(true);

        // Show success message
        displaySuccessToast(t(I18nKey.AUTH$AUTHENTICATION_SUCCESSFUL));

        // Redirect to home page
        navigate("/");
      } catch (error) {
        // Log error and show error toast
        displayErrorToast(t(I18nKey.AUTH$AUTHENTICATION_FAILED));
        navigate("/");
      } finally {
        setIsProcessing(false);
      }
    };

    processOAuthCallback();
  }, [navigate, searchParams, setProvidersAreSet, t]);

  return (
    <div className="flex flex-col items-center justify-center h-full">
      {isProcessing && (
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-lg">{t(I18nKey.AUTH$PROCESSING_AUTHENTICATION)}</p>
        </div>
      )}
    </div>
  );
}
