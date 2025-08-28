import { lazy, Suspense } from "react";
import { useSelector } from "react-redux";
import { cn } from "#/utils/utils";
import { useConversationTabs } from "./use-conversation-tabs";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { RootState } from "#/store";
import { ConversationLoading } from "../conversation-loading";

// Lazy load all tab components
const EditorTab = lazy(() => import("#/routes/changes-tab"));
const BrowserTab = lazy(() => import("#/routes/browser-tab"));
const JupyterTab = lazy(() => import("#/routes/jupyter-tab"));
const ServedTab = lazy(() => import("#/routes/served-tab"));
const VSCodeTab = lazy(() => import("#/routes/vscode-tab"));

export function ConversationTabContent() {
  const [{ selectedTab }] = useConversationTabs();

  const { shouldShownAgentLoading } = useSelector(
    (state: RootState) => state.conversation,
  );

  // Determine which tab is active based on the current path
  const isEditorActive = selectedTab === "editor";
  const isBrowserActive = selectedTab === "browser";
  const isJupyterActive = selectedTab === "jupyter";
  const isServedActive = selectedTab === "served";
  const isVSCodeActive = selectedTab === "vscode";

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
      <div className="overflow-hidden flex-grow rounded-b-xl">
        <div className="h-full w-full">
          <div className="h-full w-full relative">
            {/* Each tab content is always loaded but only visible when active */}
            <Suspense
              fallback={
                <div className="flex items-center justify-center h-full">
                  <LoadingSpinner size="large" />
                </div>
              }
            >
              <div
                className={`absolute inset-0 ${isEditorActive ? "block" : "hidden"}`}
              >
                <EditorTab />
              </div>
              <div
                className={`absolute inset-0 ${isBrowserActive ? "block" : "hidden"}`}
              >
                <BrowserTab />
              </div>
              <div
                className={`absolute inset-0 ${isJupyterActive ? "block" : "hidden"}`}
              >
                <JupyterTab />
              </div>
              <div
                className={`absolute inset-0 ${isServedActive ? "block" : "hidden"}`}
              >
                <ServedTab />
              </div>
              <div
                className={`absolute inset-0 ${isVSCodeActive ? "block" : "hidden"}`}
              >
                <VSCodeTab />
              </div>
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  );
}
