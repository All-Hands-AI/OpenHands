import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { useVSCodeUrl } from "#/hooks/query/use-vscode-url";
import { VSCODE_IN_NEW_TAB } from "#/utils/feature-flags";

function VSCodeTab() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useVSCodeUrl();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);
  const iframeRef = React.useRef<HTMLIFrameElement>(null);
  const [isCrossProtocol, setIsCrossProtocol] = useState(false);
  const [iframeError, setIframeError] = useState<string | null>(null);

  useEffect(() => {
    if (data?.url) {
      try {
        const iframeProtocol = new URL(data.url).protocol;
        const currentProtocol = window.location.protocol;

        // Check if the iframe URL has a different protocol than the current page
        setIsCrossProtocol(
          VSCODE_IN_NEW_TAB() || iframeProtocol !== currentProtocol,
        );
      } catch (e) {
        // Silently handle URL parsing errors
        setIframeError(t("VSCODE$URL_PARSE_ERROR"));
      }
    }
  }, [data?.url]);

  const handleOpenInNewTab = () => {
    if (data?.url) {
      window.open(data.url, "_blank", "noopener,noreferrer");
    }
  };

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

  if (error || (data && data.error) || !data?.url || iframeError) {
    return (
      <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
        {iframeError ||
          data?.error ||
          String(error) ||
          t(I18nKey.VSCODE$URL_NOT_AVAILABLE)}
      </div>
    );
  }

  // If cross-origin, show a button to open in new tab
  if (isCrossProtocol) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-4">
        <div className="text-xl text-tertiary-light text-center max-w-md">
          {t("VSCODE$CROSS_ORIGIN_WARNING")}
        </div>
        <button
          type="button"
          onClick={handleOpenInNewTab}
          className="px-4 py-2 bg-primary text-white rounded-sm hover:bg-primary-dark transition-colors"
        >
          {t("VSCODE$OPEN_IN_NEW_TAB")}
        </button>
      </div>
    );
  }

  // If same origin, use the iframe
  return (
    <div className="h-full w-full">
      <iframe
        ref={iframeRef}
        title={t(I18nKey.VSCODE$TITLE)}
        src={data.url}
        className="w-full h-full border-0"
        allow="clipboard-read; clipboard-write"
      />
    </div>
  );
}

// Export the VSCodeTab directly since we're using the provider at a higher level
export default VSCodeTab;
