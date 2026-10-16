import { useTranslation } from "react-i18next";
import { SecretForm } from "#/components/features/settings/secrets-settings/secret-form";
import { useOptionalConversationId } from "#/hooks/use-conversation-id";
import { I18nKey } from "#/i18n/declaration";
import { completeSecretRequest } from "#/services/secret-request";
import { useSecretRequestStore } from "#/stores/secret-request-store";

/**
 * Collects the secrets the agent asked for with `request_secret`, as cards at
 * the end of the chat. They do not block the conversation: the agent keeps
 * working and the user answers whenever they are ready. The value goes
 * straight to the secrets store; the agent only learns the outcome.
 */
export function SecretRequestCards() {
  const { t } = useTranslation("openhands");
  const { conversationId } = useOptionalConversationId();
  const allRequests = useSecretRequestStore((s) => s.requests);
  const requests = allRequests.filter(
    (r) => r.conversationId === conversationId,
  );

  return requests.map((request) => (
    <section
      key={request.toolCallId}
      data-testid="secret-request-card"
      aria-label={t(I18nKey.SECRETS$REQUEST_TITLE)}
      className="mt-4 flex flex-col gap-3 rounded-xl border border-border bg-surface p-4"
    >
      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium text-contrast">
          {t(I18nKey.SECRETS$REQUEST_TITLE)}
        </span>
        {request.reason ? (
          <span className="text-sm text-muted">{request.reason}</span>
        ) : null}
      </div>
      {/* SecretForm also calls onCancel after a successful save; the request
          is already complete by then, so that call is a no-op. */}
      <SecretForm
        mode="add"
        selectedSecret={null}
        defaultName={request.name}
        keepOpenOnError
        onSaved={(secret) => void completeSecretRequest(request, secret)}
        onCancel={() => void completeSecretRequest(request, null)}
      />
    </section>
  ));
}
