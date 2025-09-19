import { ChatInterface } from "../../chat/chat-interface";

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
