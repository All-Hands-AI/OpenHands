import posthog from "posthog-js";

/**
 * Handle user consent for tracking
 * @param consent Whether the user consents to tracking
 */
export const handleCaptureConsent = (consent: boolean) => {
  if (consent && !posthog.has_opted_in_capturing()) {
    posthog.opt_in_capturing();
  }

  if (!consent && !posthog.has_opted_out_capturing()) {
    posthog.opt_out_capturing();
  }
};
