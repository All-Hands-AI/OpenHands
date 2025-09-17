import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { ChatInterfaceWrapper } from "./chat-interface-wrapper";
import { ConversationTabContent } from "../conversation-tabs/conversation-tab-content/conversation-tab-content";

interface DesktopLayoutProps {
  isRightPanelShown: boolean;
}

export function DesktopLayout({ isRightPanelShown }: DesktopLayoutProps) {
  return (
    <PanelGroup
      direction="horizontal"
      className="grow h-full min-h-0 min-w-0"
      autoSaveId="react-resizable-panels:layout"
    >
      <Panel minSize={30} maxSize={80} className="overflow-hidden bg-base">
        <ChatInterfaceWrapper isRightPanelShown={isRightPanelShown} />
      </Panel>
      {isRightPanelShown && (
        <>
          <PanelResizeHandle className="cursor-ew-resize" />
          <Panel
            minSize={20}
            maxSize={70}
            className="flex flex-col overflow-hidden"
          >
            <div className="flex flex-col flex-1 gap-3">
              <ConversationTabContent />
            </div>
          </Panel>
        </>
      )}
    </PanelGroup>
  );
}
