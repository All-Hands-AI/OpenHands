import { lazy } from "react";
import { useSelector } from "react-redux";
import { RootState } from "#/store";
import { ConversationLoading } from "../../conversation-loading";
import Terminal from "../../../terminal/terminal";
import { TabWrapper } from "./tab-wrapper";
import { TabContainer } from "./tab-container";
import { TabContentArea } from "./tab-content-area";

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

  // Define tab configurations
  const tabs = [
    { key: "editor", component: EditorTab, isActive: selectedTab === "editor" },
    {
      key: "browser",
      component: BrowserTab,
      isActive: selectedTab === "browser",
    },
    {
      key: "jupyter",
      component: JupyterTab,
      isActive: selectedTab === "jupyter",
    },
    { key: "served", component: ServedTab, isActive: selectedTab === "served" },
    { key: "vscode", component: VSCodeTab, isActive: selectedTab === "vscode" },
    {
      key: "terminal",
      component: Terminal,
      isActive: selectedTab === "terminal",
    },
  ];

  if (shouldShownAgentLoading) {
    return <ConversationLoading />;
  }

  return (
    <TabContainer>
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
