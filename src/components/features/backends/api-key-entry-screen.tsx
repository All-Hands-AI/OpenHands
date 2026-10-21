import React from "react";
import { useTranslation } from "react-i18next";
import { SettingsClient } from "@openhands/typescript-client/clients";
import { I18nKey } from "#/i18n/declaration";
import { isSdkHttpStatusError } from "#/api/agent-server-compatibility";
import { getAgentServerClientOptions } from "#/api/agent-server-client-options";
import { isNoBackend, NO_BACKEND } from "#/api/backend-registry/active-store";
import { useActiveBackendContext } from "#/contexts/active-backend-context";
import { BrandButton } from "#/components/features/settings/brand-button";
import {
  MODAL_MAX_WIDTH_VIEWPORT,
  modalWidthClassName,
} from "#/components/shared/modals/modal-body";
import { cn } from "#/utils/utils";
import { BackendStatusDot } from "./backend-status-dot";
import {
  BackendForm,
  type BackendFormSubmitPayload,
} from "./backend-form-modal";

/**
 * Full-screen prompt shown when the server is in public mode
 * (`VITE_AUTH_REQUIRED=true`) and no valid API key has been configured.
 *
 * Reuses {@link BackendForm} with `hostReadOnly` + `onSubmitOverride`
 * to render the standard name / host / API-key inputs while adding
 * server-side validation (calls `GET /api/settings` before persisting)
 * and a connection status indicator.
 */
export default function ApiKeyEntryScreen() {
  const { t } = useTranslation("openhands");
  const { active, backends, addBackend, updateBackend, setActive } =
    useActiveBackendContext();

  const host = window.location.origin;
  const rootBackend = backends.find((backend) => {
    if (backend.kind !== "local" || backend.marsSessionId) return false;
    try {
      const url = new URL(backend.host);
      return url.origin === host && url.pathname === "/";
    } catch {
      return false;
    }
  });

  const [isValidating, setIsValidating] = React.useState(false);
  const [connectionStatus, setConnectionStatus] = React.useState<
    "idle" | "success" | "error"
  >("idle");
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const handleSubmitOverride = React.useCallback(
    async (payload: BackendFormSubmitPayload) => {
      setIsValidating(true);
      setConnectionStatus("idle");
      setErrorMessage(null);

      try {
        await new SettingsClient(
          getAgentServerClientOptions({
            host: payload.host,
            sessionApiKey: payload.apiKey,
            timeout: 5000,
          }),
        ).getSettings();

        setConnectionStatus("success");

        // This form authenticates the serving Canvas, even when a DigitalOcean
        // guest is active. Its host, credentials, and session metadata must stay
        // on their own record so a reload can reconnect to the same session.
        // Validation above uses the local Agent Server protocol even when
        // the Canvas hostname resembles an OpenHands Cloud deployment.
        const rootPayload = { ...payload, kind: "local" as const };
        if (rootBackend) {
          updateBackend(rootBackend.id, rootPayload);
        } else {
          addBackend(rootPayload);
          if (!isNoBackend(active.backend)) {
            setActive(active.backend.id, active.orgId);
          }
        }

        window.location.reload();
      } catch (err: unknown) {
        setConnectionStatus("error");

        if (isSdkHttpStatusError(err, 401)) {
          setErrorMessage(t(I18nKey.AUTH$INVALID_KEY));
        } else {
          const detail = err instanceof Error ? err.message : String(err);
          setErrorMessage(
            `${t(I18nKey.AUTH$CONNECTION_FAILED)}${detail ? `: ${detail}` : ""}`,
          );
        }
        setIsValidating(false);
      }
    },
    [active, rootBackend, addBackend, updateBackend, setActive, t],
  );

  return (
    <div
      data-testid="api-key-entry-screen"
      className="flex min-h-screen items-center justify-center bg-canvas-base px-6"
    >
      <div
        className={cn(
          "relative rounded-xl border border-border bg-base-secondary",
          modalWidthClassName("md"),
          MODAL_MAX_WIDTH_VIEWPORT,
        )}
      >
        <div className="px-6 pt-6 pb-2 pr-12">
          <h2 className="text-lg font-semibold">
            {t(I18nKey.BACKEND$ADD_TITLE)}
          </h2>
        </div>

        <div className="px-6 pb-6 pt-2">
          <BackendForm
            mode="add"
            backend={{
              ...(rootBackend ?? NO_BACKEND),
              host,
              apiKey: "",
              name: "",
            }}
            onSubmitted={() => {}}
            testIdRoot="api-key-entry"
            hostReadOnly
            requireApiKey
            onSubmitOverride={handleSubmitOverride}
            renderActions={({ canSubmit, testIdRoot }) => (
              <>
                {connectionStatus !== "idle" && (
                  <div className="flex items-center gap-3 text-sm">
                    <BackendStatusDot
                      isConnected={connectionStatus === "success"}
                    />
                    <span
                      data-testid={`${testIdRoot}-status`}
                      className={
                        connectionStatus === "error"
                          ? "text-feedback-error"
                          : "text-feedback-success"
                      }
                    >
                      {connectionStatus === "error"
                        ? errorMessage
                        : t(I18nKey.ONBOARDING$BACKEND_STATUS_CONNECTED)}
                    </span>
                  </div>
                )}

                <BrandButton
                  type="submit"
                  variant="secondary"
                  isDisabled={!canSubmit || isValidating}
                  testId={`${testIdRoot}-submit`}
                  className="w-full text-center"
                >
                  {isValidating
                    ? t(I18nKey.ONBOARDING$BACKEND_STATUS_CHECKING)
                    : t(I18nKey.BACKEND$CONNECT)}
                </BrandButton>
              </>
            )}
          />
        </div>
      </div>
    </div>
  );
}
