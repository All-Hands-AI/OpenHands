import { lazy, Suspense } from "react";
import { useSelector } from "react-redux";
import { cn } from "#/utils/utils";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { RootState } from "#/store";
import { ConversationLoading } from "../conversation-loading";
import Terminal from "../../terminal/terminal";

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

  // Determine which tab is active based on the current path
  const isEditorActive = selectedTab === "editor";
  const isBrowserActive = selectedTab === "browser";
  const isJupyterActive = selectedTab === "jupyter";
  const isServedActive = selectedTab === "served";
  const isVSCodeActive = selectedTab === "vscode";
  const isTerminalActive = selectedTab === "terminal";

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
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  );
}
