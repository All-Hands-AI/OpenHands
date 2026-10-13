import type { CustomSecretInput } from "#/api/agent-server-adapter";
import AgentServerConversationService from "#/api/conversation-service/agent-server-conversation-service.api";
import {
  REQUEST_SECRET_TOOL_NAME,
  SECRET_REQUEST_RESULT_PREFIX,
} from "#/constants/secret-request";
import { updateConversationSecrets } from "#/hooks/mutation/conversation-mutation-utils";
import { useGoalStore } from "#/stores/goal-store";
import {
  type SecretRequest,
  useSecretRequestStore,
} from "#/stores/secret-request-store";
import type { RequestSecretAction } from "#/types/agent-server/core";
import { claimClientToolCall } from "#/utils/claim-client-tool-call";

const LEDGER_STORAGE_KEY_PREFIX = "openhands-secret-requests:";

type SecretRequestResult =
  | { status: "saved"; name: string }
  | { status: "not_saved"; name: string; guidance: string }
  | { status: "error"; name: string; error: string; guidance: string };

/**
 * Execute a `request_secret` tool call by queueing the secret request modal.
 * The outcome is reported by {@link completeSecretRequest} once the user
 * closes it.
 */
export function handleRequestSecretAction(
  action: RequestSecretAction,
  conversationId: string,
  toolCallId: string,
): void {
  // A replayed call would reopen the modal and report the outcome twice.
  if (
    !claimClientToolCall(
      `${LEDGER_STORAGE_KEY_PREFIX}${conversationId}`,
      toolCallId,
    )
  ) {
    return;
  }

  useSecretRequestStore.getState().enqueue({
    conversationId,
    toolCallId,
    name: action.name,
    reason: action.reason ?? null,
  });
}

async function resolveResult(
  request: SecretRequest,
  savedSecret: CustomSecretInput | null,
): Promise<SecretRequestResult> {
  if (!savedSecret) {
    return {
      status: "not_saved",
      name: request.name,
      guidance:
        "The user closed the form without saving the secret. Ask them how they want to proceed; never ask them to paste it into the chat.",
    };
  }

  try {
    await updateConversationSecrets(request.conversationId, [savedSecret]);
    return { status: "saved", name: savedSecret.name };
  } catch (error) {
    return {
      status: "error",
      name: savedSecret.name,
      error: error instanceof Error ? error.message : String(error),
      guidance:
        "The secret was saved to the user's settings but could not be attached to this conversation. It will be available in new conversations; tell the user.",
    };
  }
}

/**
 * Hand the outcome of a secret request back to the agent. Client tools are
 * acknowledged before the user answers, so a message is the only way to tell
 * the agent whether the secret is now available. It never carries the value.
 *
 * Never rejects: the user already closed the modal, so a failure to report is
 * logged rather than surfaced.
 */
export async function completeSecretRequest(
  request: SecretRequest,
  savedSecret: CustomSecretInput | null,
): Promise<void> {
  // SecretForm can settle after a cancel; report each request only once.
  const store = useSecretRequestStore.getState();
  if (!store.requests.some((r) => r.toolCallId === request.toolCallId)) return;
  store.dismiss(request.toolCallId);

  const result = await resolveResult(request, savedSecret);

  // The agent-server cancels an active `/goal` loop on any inbound message.
  const goalStatus =
    useGoalStore.getState().statusByConversation[request.conversationId];
  if (goalStatus?.active) return;

  await AgentServerConversationService.sendMessage(request.conversationId, {
    role: "user",
    content: [
      {
        type: "text",
        text: `${SECRET_REQUEST_RESULT_PREFIX}${JSON.stringify(result)}`,
      },
    ],
  }).catch((error) => {
    console.warn(
      `[${REQUEST_SECRET_TOOL_NAME}] Failed to report the request result:`,
      error,
    );
  });
}
