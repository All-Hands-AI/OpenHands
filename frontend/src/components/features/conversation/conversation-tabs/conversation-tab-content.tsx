import { lazy, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { cn } from "#/utils/utils";
import { RootState } from "#/store";
import { ConversationLoading } from "../conversation-loading";
import Terminal from "../../terminal/terminal";
import { ConversationTabTitle } from "./conversation-tab-title";
import { I18nKey } from "#/i18n/declaration";

// Lazy load all tab components
const EditorTab = lazy(() => import("#/routes/changes-tab"));
const BrowserTab = lazy(() => import("#/routes/browser-tab"));
const JupyterTab = lazy(() => import("#/routes/jupyter-tab"));
const ServedTab = lazy(() => import("#/routes/served-tab"));
const VSCodeTab = lazy(() => import("#/routes/vscode-tab"));

export function ConversationTabContent() {
  const selectedTab = useSelector(
    (state: RootState) => state.conversation.selectedTab,
  );
  const { shouldShownAgentLoading } = useSelector(
    (state: RootState) => state.conversation,
  );

  const { t } = useTranslation();

  // Determine which tab is active based on the current path
  const isEditorActive = selectedTab === "editor";
  const isBrowserActive = selectedTab === "browser";
  const isJupyterActive = selectedTab === "jupyter";
  const isServedActive = selectedTab === "served";
  const isVSCodeActive = selectedTab === "vscode";
  const isTerminalActive = selectedTab === "terminal";

  const conversationTabTitle = useMemo(() => {
    if (isEditorActive) {
      return t(I18nKey.COMMON$CHANGES);
    }
    if (isBrowserActive) {
      return t(I18nKey.COMMON$BROWSER);
    }
    if (isJupyterActive) {
      return t(I18nKey.COMMON$JUPYTER);
    }
    if (isServedActive) {
      return t(I18nKey.COMMON$APP);
    }
    if (isVSCodeActive) {
      return t(I18nKey.COMMON$CODE);
    }
    if (isTerminalActive) {
      return t(I18nKey.COMMON$TERMINAL);
    }
    return "";
  }, [
    isEditorActive,
    isBrowserActive,
    isJupyterActive,
    isServedActive,
    isVSCodeActive,
    isTerminalActive,
  ]);

  if (shouldShownAgentLoading) {
    return <ConversationLoading />;
  }

  return (
    <div
      className={cn(
        "bg-[#25272D] border border-[#525252] rounded-xl flex flex-col h-full w-full",
        "h-full w-full",
      )}
    >
      <ConversationTabTitle title={conversationTabTitle} />

      <div className="overflow-hidden flex-grow rounded-b-xl">
        <div className="h-full w-full">
          <div className="h-full w-full relative">
            {/* Each tab content is always loaded but only visible when active */}
            <div
              className={cn(
                "absolute inset-0",
                isEditorActive ? "block" : "hidden",
              )}
            >
              <EditorTab />
            </div>
            <div
              className={cn(
                "absolute inset-0",
                isBrowserActive ? "block" : "hidden",
              )}
            >
              <BrowserTab />
            </div>
            <div
              className={cn(
                "absolute inset-0",
                isJupyterActive ? "block" : "hidden",
              )}
            >
              <JupyterTab />
            </div>
            <div
              className={cn(
                "absolute inset-0",
                isServedActive ? "block" : "hidden",
              )}
            >
              <ServedTab />
            </div>
            <div
              className={cn(
                "absolute inset-0",
                isVSCodeActive ? "block" : "hidden",
              )}
            >
              <VSCodeTab />
            </div>
            <div
              className={cn(
                "absolute inset-0",
                isTerminalActive ? "block" : "hidden",
              )}
            >
              <Terminal />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
