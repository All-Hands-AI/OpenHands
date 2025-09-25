import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import ConversationService from "#/api/conversation-service/conversation-service.api";
import { useConversationId } from "#/hooks/use-conversation-id";
import { I18nKey } from "#/i18n/declaration";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";
import { useRuntimeIsReady } from "#/hooks/use-runtime-is-ready";

// Define the return type for the VS Code URL query
interface VSCodeUrlResult {
  url: string | null;
  error: string | null;
}

export const useVSCodeUrl = () => {
  const { t } = useTranslation();
  const { conversationId } = useConversationId();
  const runtimeIsReady = useRuntimeIsReady();

  return useQuery<VSCodeUrlResult>({
    queryKey: ["vscode_url", conversationId],
    queryFn: async () => {
      if (!conversationId) throw new Error("No conversation ID");
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
    enabled: runtimeIsReady && !!conversationId,
    refetchOnMount: true,
    retry: 3,
  });
};
