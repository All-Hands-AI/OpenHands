import React from "react";
import posthog from "posthog-js";
import { useSettings } from "#/hooks/query/use-settings";

/**
 * Check if the user has consented to analytics tracking
 * @returns true if user has consented, false otherwise
 */
export const hasUserConsentedToAnalytics = (): boolean => {
  // Try to get settings from React Query cache if available
  // This is a fallback - the proper way is to use the hook in components
  try {
    // Access the query client to get cached settings
    // This is a workaround for when we can't use hooks
    const queryClient = (window as any).__REACT_QUERY_CLIENT__;
    if (queryClient) {
      const settings = queryClient.getQueryData(["settings"]);
      if (settings && typeof settings === "object" && "USER_CONSENTS_TO_ANALYTICS" in settings) {
        return settings.USER_CONSENTS_TO_ANALYTICS === true;
      }
    }
  } catch {
    // Ignore errors when trying to access query client
  }

  // Default to false (no consent) if we can't determine
  return false;
};

/**
 * Safely capture a PostHog event only if user has consented to analytics
 * @param eventName - Name of the event to capture
 * @param properties - Optional properties to include with the event
 */
export const safePostHogCapture = (
  eventName: string,
  properties?: Record<string, unknown>,
): void => {
  // Check if user has opted out
  if (posthog.has_opted_out_capturing()) {
    return;
  }

  // Only capture if user has explicitly opted in
  if (posthog.has_opted_in_capturing()) {
    posthog.capture(eventName, properties);
  }
};

/**
 * Safely identify a user in PostHog only if user has consented to analytics
 * @param distinctId - Unique identifier for the user
 * @param properties - Optional properties to associate with the user
 */
export const safePostHogIdentify = (
  distinctId: string,
  properties?: Record<string, unknown>,
): void => {
  // Check if user has opted out
  if (posthog.has_opted_out_capturing()) {
    return;
  }

  // Only identify if user has explicitly opted in
  if (posthog.has_opted_in_capturing()) {
    posthog.identify(distinctId, properties);
  }
};

/**
 * Safely capture an exception in PostHog only if user has consented to analytics
 * @param error - The error to capture
 * @param properties - Optional properties to include with the error
 */
export const safePostHogCaptureException = (
  error: Error,
  properties?: Record<string, unknown>,
): void => {
  // Check if user has opted out
  if (posthog.has_opted_out_capturing()) {
    return;
  }

  // Only capture if user has explicitly opted in
  if (posthog.has_opted_in_capturing()) {
    posthog.captureException(error, properties);
  }
};

/**
 * Hook to get safe PostHog capture functions that respect user consent
 * This should be used in React components where settings are available
 */
export const useSafePostHog = () => {
  const { data: settings } = useSettings();
  const hasConsented = settings?.USER_CONSENTS_TO_ANALYTICS === true;

  const capture = React.useCallback(
    (eventName: string, properties?: Record<string, unknown>) => {
      if (hasConsented && !posthog.has_opted_out_capturing()) {
        posthog.capture(eventName, properties);
      }
    },
    [hasConsented],
  );

  const identify = React.useCallback(
    (distinctId: string, properties?: Record<string, unknown>) => {
      if (hasConsented && !posthog.has_opted_out_capturing()) {
        posthog.identify(distinctId, properties);
      }
    },
    [hasConsented],
  );

  const captureException = React.useCallback(
    (error: Error, properties?: Record<string, unknown>) => {
      if (hasConsented && !posthog.has_opted_out_capturing()) {
        posthog.captureException(error, properties);
      }
    },
    [hasConsented],
  );

  return {
    capture,
    identify,
    captureException,
  };
};
