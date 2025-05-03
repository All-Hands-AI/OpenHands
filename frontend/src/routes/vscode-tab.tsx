import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { useConversation } from "#/context/conversation-context";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { transformVSCodeUrl } from "#/utils/vscode-url-helper";

// Create a context to store the VS Code URL globally
interface VSCodeContextType {
  vsCodeUrl: string | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

const VSCodeContext = React.createContext<VSCodeContextType>({
  vsCodeUrl: null,
  isLoading: true,
  error: null,
  refetch: async () => {},
});

// Provider component to fetch and store the VS Code URL
export function VSCodeProvider({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const { conversationId } = useConversation();
  const [vsCodeUrl, setVsCodeUrl] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);

  const fetchVSCodeUrl = React.useCallback(async () => {
    if (!conversationId || isRuntimeInactive) return;

    try {
      setIsLoading(true);
      const response = await fetch(
        `/api/conversations/${conversationId}/vscode-url`,
      );
      const data = await response.json();

      if (data.vscode_url) {
        const transformedUrl = transformVSCodeUrl(data.vscode_url);
        setVsCodeUrl(transformedUrl);
      } else {
        setError(t(I18nKey.VSCODE$URL_NOT_AVAILABLE));
      }
    } catch (err) {
      setError(t(I18nKey.VSCODE$FETCH_ERROR));
      // Error is handled by setting the error state
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, isRuntimeInactive, t]);

  React.useEffect(() => {
    fetchVSCodeUrl();
  }, [fetchVSCodeUrl]);

  const contextValue = React.useMemo(() => ({
    vsCodeUrl,
    isLoading,
    error,
    refetch: fetchVSCodeUrl,
  }), [vsCodeUrl, isLoading, error, fetchVSCodeUrl]);

  return (
    <VSCodeContext.Provider value={contextValue}>
      {children}
    </VSCodeContext.Provider>
  );
}

// Hook to use the VS Code context
export function useVSCode() {
  return React.useContext(VSCodeContext);
}

function VSCodeTab() {
  const { t } = useTranslation();
  const { vsCodeUrl, isLoading, error } = useVSCode();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);
  const iframeRef = React.useRef<HTMLIFrameElement>(null);

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
        ref={iframeRef}
        title={t(I18nKey.VSCODE$TITLE)}
        src={vsCodeUrl}
        className="w-full h-full border-0"
        allow={t(I18nKey.VSCODE$IFRAME_PERMISSIONS)}
      />
    </div>
  );
}

// Export the VSCodeTab directly since we're using the provider at a higher level
export default VSCodeTab;
