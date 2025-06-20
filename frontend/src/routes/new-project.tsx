import { useDisclosure } from "@heroui/react";
import React from "react";
import { useNavigate } from "react-router";
import { useDispatch, useSelector } from "react-redux";
import { useTranslation } from "react-i18next";
import { NewProjectControls } from "#/components/features/controls/new-project-controls";
import { NewProjectChatInterface } from "#/components/features/chat/new-project-chat-interface";
import { NewProjectTopNav } from "#/components/features/nav/new-project-top-nav";
import { clearTerminal } from "#/state/command-slice";
import { useEffectOnce } from "#/hooks/use-effect-once";
import { clearJupyter } from "#/state/jupyter-slice";
import { Layers, Code, Loader } from "lucide-react";
import { TabbedInterface, CodeViewer, LoadingScreen } from "#/components/features/chat/interface-components";

import {
  Orientation,
  ResizablePanel,
} from "#/components/layout/resizable-panel";
import Security from "#/components/shared/modals/security/security";
import { useSettings } from "#/hooks/query/use-settings";
import { RootState } from "#/store";
import { displayErrorToast } from "#/utils/custom-toast-handlers";
import { useIsAuthed } from "#/hooks/query/use-is-authed";

// Mock conversation ID for development
const MOCK_CONVERSATION_ID = "new-project-dev";

// Interface view types for right panel
type RightPanelView = 'main' | 'tabbed' | 'code' | 'loading';

function AppContent() {
  console.log("🔍 [DEBUG] AppContent component starting...");

  const { t } = useTranslation();
  const { data: settings } = useSettings();
  const { data: isAuthed } = useIsAuthed();
  const [isDrawerOpen, setIsDrawerOpen] = React.useState(false);
  const [rightPanelView, setRightPanelView] = React.useState<RightPanelView>('main');

  console.log("🔍 [DEBUG] Settings loaded:", !!settings);
  console.log("🔍 [DEBUG] Auth status:", isAuthed);

  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  console.log("🔍 [DEBUG] Agent state:", curAgentState);

  const [width, setWidth] = React.useState(window.innerWidth);

  // Removed authentication check - allow access without being logged in
  // React.useEffect(() => {
  //   console.log("🔍 [DEBUG] Auth effect running, isAuthed:", isAuthed);
  //   if (!isAuthed) {
  //     console.log("🔍 [DEBUG] User not authenticated, redirecting...");
  //     displayErrorToast(
  //       "You must be authenticated to access the new project interface.",
  //     );
  //     navigate("/");
  //   }
  // }, [isAuthed, navigate]);

  React.useEffect(() => {
    dispatch(clearTerminal());
    dispatch(clearJupyter());
  }, [MOCK_CONVERSATION_ID]);

  useEffectOnce(() => {
    console.log("🔍 [DEBUG] Clearing terminal and jupyter...");
    dispatch(clearTerminal());
    dispatch(clearJupyter());
  });

  function handleResize() {
    setWidth(window.innerWidth);
  }

  React.useEffect(() => {
    console.log("🔍 [DEBUG] Setting up resize listener...");
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const {
    isOpen: securityModalIsOpen,
    onOpen: onSecurityModalOpen,
    onOpenChange: onSecurityModalOpenChange,
  } = useDisclosure();

  const handleShare = () => {
    // Implement share functionality
    console.log("Share clicked");
  };

  const handleRun = () => {
    // Implement run functionality
    console.log("Run clicked");
  };

  const handleDrawerToggle = () => {
    setIsDrawerOpen(!isDrawerOpen);
  };

  const handleRightPanelViewChange = (view: RightPanelView) => {
    setRightPanelView(view);
  };

  function renderRightPanel() {
    if (rightPanelView === 'tabbed') {
      return <TabbedInterface onBack={() => handleRightPanelViewChange('main')} />;
    }

    if (rightPanelView === 'code') {
      return <CodeViewer onBack={() => handleRightPanelViewChange('main')} />;
    }

    if (rightPanelView === 'loading') {
      return <LoadingScreen onBack={() => handleRightPanelViewChange('main')} />;
    }

    // Default main view
    return (
      <div className="h-full w-full bg-base-secondary rounded-xl flex items-center justify-center">
        <div className="text-center">
          <h3 className="text-lg font-semibold text-content mb-2">Project Interface</h3>
          <p className="text-sm text-content-secondary mb-6">
            This is the experimental project interface.
          </p>
          <div className="space-y-3">
            <button
              onClick={() => handleRightPanelViewChange('tabbed')}
              className="flex items-center justify-center gap-2 bg-base rounded-lg px-4 py-3 text-sm font-medium border border-border hover:bg-base-tertiary transition-colors w-full"
            >
              <Layers className="w-4 h-4" />
              Tabbed UI
            </button>
            <button
              onClick={() => handleRightPanelViewChange('code')}
              className="flex items-center justify-center gap-2 bg-base rounded-lg px-4 py-3 text-sm font-medium border border-border hover:bg-base-tertiary transition-colors w-full"
            >
              <Code className="w-4 h-4" />
              Code View
            </button>
            <button
              onClick={() => handleRightPanelViewChange('loading')}
              className="flex items-center justify-center gap-2 bg-base rounded-lg px-4 py-3 text-sm font-medium border border-border hover:bg-base-tertiary transition-colors w-full"
            >
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
              Loading Screen
            </button>
          </div>
        </div>
      </div>
    );
  }

  function renderMain() {
    console.log("🔍 [DEBUG] Rendering main content, width:", width);
    if (width <= 640) {
      return (
        <div className="rounded-xl overflow-hidden w-full">
          <NewProjectChatInterface />
        </div>
      );
    }

    // If drawer is closed, only show the main chat interface
    if (!isDrawerOpen) {
      return (
        <div className="flex justify-center w-full">
          <div className="rounded-xl overflow-hidden w-full max-w-[800px]">
            <NewProjectChatInterface />
          </div>
        </div>
      );
    }

    // If drawer is open, show both panels
    return (
      <ResizablePanel
        orientation={Orientation.HORIZONTAL}
        className="grow h-full min-h-0 min-w-0"
        initialSize={500}
        firstClassName="rounded-xl overflow-hidden"
        secondClassName="flex flex-col overflow-hidden"
        firstChild={<NewProjectChatInterface />}
        secondChild={renderRightPanel()}
      />
    );
  }

  console.log("🔍 [DEBUG] About to render main component...");

  return (
    <div data-testid="new-project-route" className="flex flex-col h-full">
      <NewProjectTopNav
        onShare={handleShare}
        onRun={handleRun}
        onDrawerToggle={handleDrawerToggle}
      />
      <div className="flex h-full overflow-auto gap-3 p-3">{renderMain()}</div>

      <NewProjectControls
        setSecurityOpen={onSecurityModalOpen}
        showSecurityLock={!!settings?.SECURITY_ANALYZER}
      />
      {settings && (
        <Security
          isOpen={securityModalIsOpen}
          onOpenChange={onSecurityModalOpenChange}
          securityAnalyzer={settings.SECURITY_ANALYZER}
        />
      )}
    </div>
  );
}

function App() {
  console.log("🔍 [DEBUG] App component starting...");
  return <AppContent />;
}

export default App;
