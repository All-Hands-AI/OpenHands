import posthog from "posthog-js";
import toast from "react-hot-toast";
import { jsx as _jsx } from "react/jsx-runtime";
import { ErrorToast } from "#/components/shared/error-toast";
import { handleStatusMessage } from "#/services/actions";

interface ErrorDetails {
  message: string;
  source?: string;
  metadata?: Record<string, unknown>;
  msgId?: string;
}

export function logError({ message, source, metadata = {} }: ErrorDetails) {
  posthog.capture("error_occurred", {
    error_message: message,
    error_source: source || "unknown",
    ...metadata,
  });
}

export function showErrorToast({
  message,
  source,
  metadata = {},
}: ErrorDetails) {
  logError({ message, source, metadata });
  toast.custom((t: { id: string }) =>
    _jsx(ErrorToast, { id: t.id, error: message }),
  );
}

export function showChatError({
  message,
  source,
  metadata = {},
  msgId,
}: ErrorDetails) {
  logError({ message, source, metadata });
  handleStatusMessage({
    type: "error",
    message,
    id: msgId,
    status_update: true,
  });
}
