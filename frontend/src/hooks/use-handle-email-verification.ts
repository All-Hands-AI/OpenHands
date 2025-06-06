import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router";
import { AxiosError } from "axios";
import { openHands } from "#/api/open-hands-axios";
import { Settings } from "#/types/settings";
import { useConfig } from "#/hooks/query/use-config";

/**
 * Hook to handle email verification errors (403 with "Email has not been verified" message)
 * This hook sets up an axios interceptor that will reload settings and navigate to the user settings page
 * when a 403 error with the specific message is encountered.
 */
export const useHandleEmailVerification = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { data: config } = useConfig();
  const appMode = config?.APP_MODE;
  console.log(`config: ${config}`);
  console.log(`AppMode: ${appMode}`);

  useEffect(() => {
    // Add response interceptor
    const interceptorId = openHands.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.log(
          `Received error ${error.response?.status} with message ${error.response?.data}`,
        );

        const EMAIL_NOT_VERIFIED = "EmailNotVerifiedError";
        // check for email verification error message no matter how it is returned.
        const isEmailNotVerified = (() => {
          const data = error.response?.data;

          if (typeof data === "string") {
            return data.includes(EMAIL_NOT_VERIFIED);
          }

          if (typeof data === "object" && data !== null) {
            if ("message" in data) {
              const { message } = data;
              if (typeof message === "string") {
                return message.includes(EMAIL_NOT_VERIFIED);
              }
              if (Array.isArray(message)) {
                return message.some(
                  (msg) =>
                    typeof msg === "string" && msg.includes(EMAIL_NOT_VERIFIED),
                );
              }
            }

            // Search any values in object in case message key is different
            return Object.values(data).some(
              (value) =>
                (typeof value === "string" &&
                  value.includes(EMAIL_NOT_VERIFIED)) ||
                (Array.isArray(value) &&
                  value.some(
                    (v) =>
                      typeof v === "string" && v.includes(EMAIL_NOT_VERIFIED),
                  )),
            );
          }

          return false;
        })();

        // Check if it's a 403 error with the specific message
        if (error.response?.status === 403 && isEmailNotVerified) {
          console.log("EMAIL VERIFICATION ERROR");
          // Only handle this in SAAS mode
          console.log(`config1: ${config}`);
          console.log(`AppMode1: ${appMode}`);
          if (appMode === "saas") {
            // Update settings to mark email as unverified
            queryClient.setQueryData(
              ["settings"],
              (oldData: Settings | undefined) => {
                if (oldData) {
                  console.log("ADDING EMAIL_VERIFIED is FALSE");
                  return {
                    ...oldData,
                    EMAIL_VERIFIED: false,
                  };
                }
                console.log("NO CHANGES TO SETTINGS");
                return oldData;
              },
            );

            // Invalidate settings to reload them
            queryClient.invalidateQueries({ queryKey: ["settings"] });

            // Navigate to settings/user page
            // The EmailVerificationGuard will handle the redirect
            console.log("NAVIGATING to /settings/user");
            navigate("/settings/user");
          }
        } else {
          console.log("NOT EMAIL VERIFICATION ERROR");
          console.log(typeof error.response?.data);
        }

        // Continue with the error for other error handlers
        return Promise.reject(error);
      },
    );

    // Clean up interceptor when component unmounts
    return () => {
      openHands.interceptors.response.eject(interceptorId);
    };
  }, [queryClient, navigate]);
};
