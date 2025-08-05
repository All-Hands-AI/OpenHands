import posthog from "posthog-js";
import { handleStatusMessage } from "#/services/actions";
import { displayErrorToast } from "./custom-toast-handlers";

interface ErrorDetails {
  message: string;
  source?: string;
  metadata?: Record<string, unknown>;
  msgId?: string;
}

/**
 * Track an error to PostHog for analytics purposes.
 * Respects user's analytics consent - errors are only tracked if the user
 * has opted in to analytics via the "Send anonymous data" setting.
 */
export function trackError({ message, source, metadata = {} }: ErrorDetails) {
  // Only track errors if user has opted in to analytics
  if (posthog.has_opted_out_capturing()) {
    return;
  }

  const error = new Error(message);
  posthog.captureException(error, {
    error_source: source || "unknown",
    ...metadata,
  });
}

export function showErrorToast({
  message,
  source,
  metadata = {},
}: ErrorDetails) {
  trackError({ message, source, metadata });
  displayErrorToast(message);
}

export function showChatError({
  message,
  source,
  metadata = {},
  msgId,
}: ErrorDetails) {
  trackError({ message, source, metadata });
  handleStatusMessage({
    type: "error",
    message,
    id: msgId,
    status_update: true,
  });
}
