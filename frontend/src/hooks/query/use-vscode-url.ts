import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";

// Define the return type for the VS Code URL query
interface VSCodeUrlResult {
  url: string | null;
  error: string | null;
}

export const useVSCodeUrl = () => {
  const { t } = useTranslation();
  const { conversationId } = useConversation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return useQuery<VSCodeUrlResult>({
    queryKey: ["vscode_url", conversationId],
    queryFn: async () => {
      if (!conversationId) throw new Error("No conversation ID");
      const data = await OpenHands.getVSCodeUrl(conversationId);
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
    enabled: !!conversationId && !isRuntimeInactive,
    refetchOnMount: true,
    retry: 3,
  });
};
