import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useCallback } from "react";
import OpenHands from "#/api/open-hands";
import { BrandButton } from "#/components/features/settings/brand-button";
import { I18nKey } from "#/i18n/declaration";

export default function TOSPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Temporarily disable the auth interceptor when on the TOS page
  const handleAcceptTOS = useCallback(async () => {
    try {
      const success = await OpenHands.acceptTOS();
      if (success) {
        // Get the last page from localStorage or default to root
        const lastPage = localStorage.getItem("openhandsLastPage") || "/";
        navigate(lastPage);
      }
    } catch (error) {
      console.error("Failed to accept TOS:", error);
    }
  }, [navigate]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="max-w-2xl bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold mb-6">{t(I18nKey.TOS$HEADER)}</h1>

        <div className="prose dark:prose-invert mb-8">
          <p>{t(I18nKey.TOS$WELCOME)}</p>

          <div className="my-6">
            <p className="mb-4">{t(I18nKey.TOS$REVIEW)}</p>
            <a
              href="https://www.all-hands.dev/tos"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 underline"
            >
              https://www.all-hands.dev/tos
            </a>
          </div>

          <p className="mt-6">{t(I18nKey.TOS$MESSAGE)}</p>
        </div>

        <div className="flex justify-center">
          <BrandButton
            variant="primary"
            type="button"
            onClick={handleAcceptTOS}
          >
            {t(I18nKey.TOS$ACCEPT_BUTTON)}
          </BrandButton>
        </div>
      </div>
    </div>
  );
}
