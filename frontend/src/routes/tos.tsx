import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";
import { useCallback, useEffect } from "react";
import axios from "axios";
import { useQueryClient } from "@tanstack/react-query";
import { BrandButton } from "#/components/features/settings/brand-button";
import { I18nKey } from "#/i18n/declaration";
import { DEFAULT_SETTINGS } from "#/services/settings";

export default function TOSPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Set default values for queries to prevent API calls
  useEffect(() => {
    // Set default values for config
    queryClient.setQueryData(["config"], {
      APP_MODE: "saas",
      GITHUB_CLIENT_ID: null,
      FEATURE_FLAGS: {
        ENABLE_BILLING: false,
      },
    });

    // Set default values for settings
    queryClient.setQueryData(["settings"], DEFAULT_SETTINGS);

    // Set default values for authentication
    queryClient.setQueryData(["user", "authenticated"], true);

    // Set default values for balance
    queryClient.setQueryData(["user", "balance"], { credits: 0 });

    // Prevent any API calls while on this page
    const originalFetch = window.fetch;
    window.fetch = function (input, init) {
      // Allow only the accept_tos endpoint
      if (typeof input === "string" && input.includes("/api/accept_tos")) {
        return originalFetch(input, init);
      }
      // Silent block of fetch calls on TOS page
      return Promise.resolve(
        new Response(JSON.stringify({ blocked: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    };

    return () => {
      // Restore original fetch
      window.fetch = originalFetch;

      // Clear the cache when leaving the TOS page
      queryClient.invalidateQueries({ queryKey: ["config"] });
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      queryClient.invalidateQueries({ queryKey: ["user", "authenticated"] });
      queryClient.invalidateQueries({ queryKey: ["user", "balance"] });
    };
  }, [queryClient]);

  // Use a direct axios call instead of the OpenHands API client
  // to avoid triggering the interceptors and other API calls
  const handleAcceptTOS = useCallback(async () => {
    try {
      // Create a new axios instance without interceptors
      const baseURL = `${window.location.protocol}//${window?.location.host}`;
      const response = await axios.post(`${baseURL}/api/accept_tos`);

      if (response.status === 200) {
        // Get the last page from localStorage or default to root
        const lastPage = localStorage.getItem("openhandsLastPage") || "/";

        // Instead of using navigate, do a full page reload to ensure
        // all auth state is properly refreshed
        window.location.href = lastPage;
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
