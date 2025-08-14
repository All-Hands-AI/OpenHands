import { useEffect, useState, Suspense } from "react";
import { useSelector } from "react-redux";
import { ChatInterface } from "../chat/chat-interface";
import { ConversationTabContent } from "./conversation-tabs/conversation-tab-content";
import {
  Orientation,
  ResizablePanel,
} from "#/components/layout/resizable-panel";
import { cn } from "#/utils/utils";
import { RootState } from "#/store";
import Terminal from "../terminal/terminal";
import { useConversationTabs } from "./conversation-tabs/use-conversation-tabs";

interface ChatInterfaceWrapperProps {
  isRightPanelShown: boolean;
}

export function ChatInterfaceWrapper({
  isRightPanelShown,
}: ChatInterfaceWrapperProps) {
  if (!isRightPanelShown) {
    return (
      <div className="flex justify-center w-full h-full">
        <div className="max-w-[768px]">
          <ChatInterface />
        </div>
      </div>
    );
  }

  return <ChatInterface />;
}

export function ConversationMain() {
  const [width, setWidth] = useState(window.innerWidth);
  const [{ terminalOpen }] = useConversationTabs();

  function handleResize() {
    setWidth(window.innerWidth);
  }

  useEffect(() => {
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  const isRightPanelShown = useSelector(
    (state: RootState) => state.conversation.isRightPanelShown,
  );

  if (width <= 1024) {
    return (
      <div className="flex flex-col gap-3 overflow-auto w-full">
        <div
          className={cn(
            "overflow-hidden w-full bg-base min-h-[494px]",
            !isRightPanelShown && "h-full",
          )}
        >
          <ChatInterface />
        </div>
        {isRightPanelShown && (
          <div className="h-full w-full min-h-[494px] flex flex-col gap-3">
            <ConversationTabContent />
            {terminalOpen && (
              <Suspense fallback={<div className="h-full" />}>
                <Terminal />
              </Suspense>
            )}
          </div>
        )}
      </div>
    );
  }

  if (isRightPanelShown) {
    return (
      <ResizablePanel
        orientation={Orientation.HORIZONTAL}
        className="grow h-full min-h-0 min-w-0"
        initialSize={(width - 101) * 0.5}
        firstClassName="overflow-hidden bg-base"
        secondClassName="flex flex-col overflow-hidden"
        firstChild={
          <ChatInterfaceWrapper isRightPanelShown={isRightPanelShown} />
        }
        secondChild={
          <div className="flex flex-col flex-1 gap-3">
            <ConversationTabContent />
            {terminalOpen && (
              <Suspense fallback={<div className="h-full" />}>
                <Terminal />
              </Suspense>
            )}
          </div>
        }
      />
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
