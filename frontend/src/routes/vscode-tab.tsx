import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { useConversation } from "#/context/conversation-context";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";

function VSCodeTab() {
  const { t } = useTranslation();
  const { conversationId } = useConversation();
  const [vsCodeUrl, setVsCodeUrl] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);

  React.useEffect(() => {
    async function fetchVSCodeUrl() {
      if (!conversationId || isRuntimeInactive) return;

      try {
        setIsLoading(true);
        const response = await fetch(
          `/api/conversations/${conversationId}/vscode-url`,
        );
        const data = await response.json();

        if (data.vscode_url) {
          setVsCodeUrl(data.vscode_url);
        } else {
          setError(t(I18nKey.VSCODE$URL_NOT_AVAILABLE));
        }
      } catch (err) {
        setError(t(I18nKey.VSCODE$FETCH_ERROR));
        // Error is handled by setting the error state
      } finally {
        setIsLoading(false);
      }
    }

    fetchVSCodeUrl();
  }, [conversationId, isRuntimeInactive, t]);

  if (isRuntimeInactive) {
    return (
      <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
        {t("DIFF_VIEWER$WAITING_FOR_RUNTIME")}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
        {t("DIFF_VIEWER$WAITING_FOR_RUNTIME")}
      </div>
    );
  }

  if (error || !vsCodeUrl) {
    return (
      <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
        {error || t(I18nKey.VSCODE$URL_NOT_AVAILABLE)}
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <iframe
        title={t(I18nKey.VSCODE$TITLE)}
        src={vsCodeUrl}
        className="w-full h-full border-0"
        allow={t(I18nKey.VSCODE$IFRAME_PERMISSIONS)}
      />
    </div>
  );
}

export default VSCodeTab;
