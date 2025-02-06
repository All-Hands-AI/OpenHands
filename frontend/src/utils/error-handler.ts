import posthog from "posthog-js";
import toast from "react-hot-toast";
import { handleStatusMessage } from "#/services/actions";

interface ErrorDetails {
  message: string;
  source?: string;
  metadata?: Record<string, unknown>;
  msgId?: string;
}

export function trackError({ message, source, metadata = {} }: ErrorDetails) {
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
  toast.error(message);
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
