import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import { useConversationId } from "#/hooks/use-conversation-id";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { I18nKey } from "#/i18n/declaration";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";
import { useRuntimeIsReady } from "#/hooks/use-runtime-is-ready";
import { useBatchAppConversations } from "./use-batch-app-conversations";
import { useBatchSandboxes } from "./use-batch-sandboxes";

interface VSCodeUrlResult {
  url: string | null;
  error: string | null;
}

/**
 * Unified hook to get VSCode URL for both legacy (V0) and V1 conversations
 * - V0: Uses the legacy getVSCodeUrl API endpoint
 * - V1: Gets the VSCode URL from sandbox exposed_urls
 */
export const useUnifiedVSCodeUrl = () => {
  const { t } = useTranslation();
  const { conversationId } = useConversationId();
  const { data: conversation } = useActiveConversation();
  const runtimeIsReady = useRuntimeIsReady();

  const isV1Conversation = conversation?.conversation_version === "V1";

  // Fetch V1 app conversation to get sandbox_id
  const { data: appConversations } = useBatchAppConversations(
    isV1Conversation && conversationId ? [conversationId] : [],
  );
  const appConversation = appConversations?.[0];
  const sandboxId = appConversation?.sandbox_id;

  // Fetch sandbox data for V1 conversations
  const { data: sandboxes } = useBatchSandboxes(sandboxId ? [sandboxId] : []);

  return useQuery<VSCodeUrlResult>({
    queryKey: [
      "unified",
      "vscode_url",
      conversationId,
      isV1Conversation,
      sandboxId,
    ],
    queryFn: async () => {
      if (!conversationId) throw new Error("No conversation ID");

      // V1: Get VSCode URL from sandbox exposed_urls
      if (isV1Conversation) {
        if (!sandboxes || sandboxes.length === 0 || !sandboxes[0]) {
          return {
            url: null,
            error: t(I18nKey.VSCODE$URL_NOT_AVAILABLE),
          };
        }

        const sandbox = sandboxes[0];
        const vscodeUrl = sandbox.exposed_urls?.find(
          (url) => url.name === "VSCODE",
        );

        if (!vscodeUrl) {
          return {
            url: null,
            error: t(I18nKey.VSCODE$URL_NOT_AVAILABLE),
          };
        }

        return {
          url: transformVSCodeUrl(vscodeUrl.url),
          error: null,
        };
      }

      // V0 (Legacy): Use the legacy API endpoint
      const data = await ConversationService.getVSCodeUrl(conversationId);

      if (data.vscode_url) {
        return {
          url: transformVSCodeUrl(data.vscode_url),
          error: null,
        };
      }

      return {
        url: null,
        error: t(I18nKey.VSCODE$URL_NOT_AVAILABLE),
      };
    },
    enabled:
      runtimeIsReady && !!conversationId && (!isV1Conversation || !!sandboxes),
    refetchOnMount: true,
    retry: 3,
  });
};
