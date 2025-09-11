import { useSelector } from "react-redux";
import { useWindowSize } from "@uidotdev/usehooks";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { ChatInterface } from "../chat/chat-interface";
import { ConversationTabContent } from "./conversation-tabs/conversation-tab-content";
import { cn } from "#/utils/utils";
import { RootState } from "#/store";

interface ChatInterfaceWrapperProps {
  isRightPanelShown: boolean;
}

export function ChatInterfaceWrapper({
  isRightPanelShown,
}: ChatInterfaceWrapperProps) {
  if (!isRightPanelShown) {
    return (
      <div className="flex justify-center w-full h-full">
        <div className="w-full max-w-[768px]">
          <ChatInterface />
        </div>
      </div>
    );
  }

  return <ChatInterface />;
}

export function ConversationMain() {
  const { width } = useWindowSize();
  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  if (width && width <= 1024) {
    return (
      <div className="flex flex-col gap-3 overflow-auto w-full">
        <div
          className={cn(
            "overflow-hidden w-full bg-base min-h-[600px]",
            !isRightPanelShown && "h-full",
          )}
        >
          <ChatInterface />
        </div>
        {isRightPanelShown && (
          <div className="h-full w-full min-h-[494px] flex flex-col gap-3">
            <ConversationTabContent />
          </div>
        )}
      </div>
    );
  }

  if (isRightPanelShown) {
    return (
      <PanelGroup
        direction="horizontal"
        className="grow h-full min-h-0 min-w-0"
        autoSaveId="react-resizable-panels:layout"
      >
        <Panel minSize={30} maxSize={80} className="overflow-hidden bg-base">
          <ChatInterfaceWrapper isRightPanelShown={isRightPanelShown} />
        </Panel>
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
      </PanelGroup>
    );
  }

  return (
    <div className="flex flex-col gap-3 overflow-auto w-full h-full">
      <div className="overflow-hidden w-full h-full bg-base">
        <ChatInterfaceWrapper isRightPanelShown={isRightPanelShown} />
      </div>
    </div>
  );
}
