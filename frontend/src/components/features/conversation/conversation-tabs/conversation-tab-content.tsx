import { lazy, Suspense } from "react";
import { cn } from "#/utils/utils";
import { useConversationTabs } from "./use-conversation-tabs";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
// Lazy load all tab components
const EditorTab = lazy(() => import("#/routes/changes-tab"));
const BrowserTab = lazy(() => import("#/routes/browser-tab"));
const JupyterTab = lazy(() => import("#/routes/jupyter-tab"));
const ServedTab = lazy(() => import("#/routes/served-tab"));
const VSCodeTab = lazy(() => import("#/routes/vscode-tab"));

export function ConversationTabContent() {
  const [{ selectedTab }] = useConversationTabs();

  // Determine which tab is active based on the current path
  const isEditorActive = selectedTab === "editor";
  const isBrowserActive = selectedTab === "browser";
  const isJupyterActive = selectedTab === "jupyter";
  const isServedActive = selectedTab === "served";
  const isVSCodeActive = selectedTab === "vscode";

  return (
    <div
      className={cn(
        "bg-base-secondary border border-neutral-600 rounded-xl flex flex-col h-full w-full",
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
