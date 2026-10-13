import { useMutation } from "@tanstack/react-query";
import type { CustomSecretInput } from "#/api/agent-server-adapter";
import { updateConversationSecrets } from "./conversation-mutation-utils";

export const useUpdateConversationSecrets = () =>
  useMutation({
    mutationFn: ({
      conversationId,
      secrets,
    }: {
      conversationId: string;
      secrets: CustomSecretInput[];
    }) => updateConversationSecrets(conversationId, secrets),
  });
