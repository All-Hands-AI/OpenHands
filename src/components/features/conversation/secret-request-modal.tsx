import React from "react";
import { useTranslation } from "react-i18next";
import type { CustomSecretInput } from "#/api/agent-server-adapter";
import { SecretForm } from "#/components/features/settings/secrets-settings/secret-form";
import {
  BaseModalDescription,
  BaseModalTitle,
} from "#/components/shared/modals/confirmation-modals/base-modal";
import { ModalBackdrop } from "#/components/shared/modals/modal-backdrop";
import { ModalBody } from "#/components/shared/modals/modal-body";
import { useSearchSecrets } from "#/hooks/query/use-get-secrets";
import { useOptionalConversationId } from "#/hooks/use-conversation-id";
import { I18nKey } from "#/i18n/declaration";
import { completeSecretRequest } from "#/services/secret-request";
import { useSecretRequestStore } from "#/stores/secret-request-store";

/**
 * Collects a secret the agent asked for with `request_secret`, over the
 * current conversation. The value goes straight to the secrets store; the
 * agent only learns the outcome.
 */
export function SecretRequestModal() {
  const { t } = useTranslation("openhands");
  const { conversationId } = useOptionalConversationId();
  const request = useSecretRequestStore((s) =>
    s.requests.find((r) => r.conversationId === conversationId),
  );
  const { data: secrets, isLoading } = useSearchSecrets();
  // SecretForm calls onCancel after every settled save, so remember whether
  // the save that just settled succeeded.
  const savedSecret = React.useRef<CustomSecretInput | null>(null);

  if (!request || isLoading) return null;

  const exists = secrets?.some((s) => s.name === request.name) ?? false;
  const title = t(I18nKey.SECRETS$REQUEST_TITLE);

  return (
    <ModalBackdrop
      closeOnEscape={false}
      closeOnBackdropClick={false}
      aria-label={title}
    >
      <ModalBody testID="secret-request-modal" width="md">
        <div className="flex flex-col gap-2 self-start">
          <BaseModalTitle title={title} />
          {request.reason ? (
            <BaseModalDescription description={request.reason} />
          ) : null}
        </div>
        <div className="w-full">
          <SecretForm
            key={request.toolCallId}
            mode={exists ? "edit" : "add"}
            selectedSecret={exists ? request.name : null}
            defaultName={request.name}
            onSaved={(secret) => {
              savedSecret.current = secret;
            }}
            onCancel={() => {
              const saved = savedSecret.current;
              savedSecret.current = null;
              void completeSecretRequest(request, saved);
            }}
          />
        </div>
      </ModalBody>
    </ModalBackdrop>
  );
}
