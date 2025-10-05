import { lazy, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { ConversationLoading } from "../../conversation-loading";
import { I18nKey } from "#/i18n/declaration";
import { TabWrapper } from "./tab-wrapper";
import { TabContainer } from "./tab-container";
import { TabContentArea } from "./tab-content-area";
import { ConversationTabTitle } from "../conversation-tab-title";
import Terminal from "#/components/features/terminal/terminal";
import { useConversationStore } from "#/state/conversation-store";

// Lazy load all tab components
const EditorTab = lazy(() => import("#/routes/changes-tab"));
const BrowserTab = lazy(() => import("#/routes/browser-tab"));
const JupyterTab = lazy(() => import("#/routes/jupyter-tab"));
const ServedTab = lazy(() => import("#/routes/served-tab"));
const VSCodeTab = lazy(() => import("#/routes/vscode-tab"));

export function ConversationTabContent() {
  const { selectedTab, shouldShownAgentLoading } = useConversationStore();

  const { t } = useTranslation();

  // Determine which tab is active based on the current path
  const isEditorActive = selectedTab === "editor";
  const isBrowserActive = selectedTab === "browser";
  const isJupyterActive = selectedTab === "jupyter";
  const isServedActive = selectedTab === "served";
  const isVSCodeActive = selectedTab === "vscode";
  const isTerminalActive = selectedTab === "terminal";

  // Define tab configurations
  const tabs = [
    { key: "editor", component: EditorTab, isActive: isEditorActive },
    {
      key: "browser",
      component: BrowserTab,
      isActive: isBrowserActive,
    },
    {
      key: "jupyter",
      component: JupyterTab,
      isActive: isJupyterActive,
    },
    { key: "served", component: ServedTab, isActive: isServedActive },
    { key: "vscode", component: VSCodeTab, isActive: isVSCodeActive },
    {
      key: "terminal",
      component: Terminal,
      isActive: isTerminalActive,
    },
  ];

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
    <TabContainer>
      <ConversationTabTitle title={conversationTabTitle} />
      <TabContentArea>
        {tabs.map(({ key, component: Component, isActive }) => (
          <TabWrapper key={key} isActive={isActive}>
            <Component />
          </TabWrapper>
        ))}
      </TabContentArea>
    </TabContainer>
  );
}
