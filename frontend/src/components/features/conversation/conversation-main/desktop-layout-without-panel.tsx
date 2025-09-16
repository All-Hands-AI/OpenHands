import { ChatInterfaceWrapper } from "./chat-interface-wrapper";

interface DesktopLayoutWithoutPanelProps {
  isRightPanelShown: boolean;
}

export function DesktopLayoutWithoutPanel({
  isRightPanelShown,
}: DesktopLayoutWithoutPanelProps) {
  return (
    <div className="flex flex-col gap-3 overflow-auto w-full h-full">
      <div className="overflow-hidden w-full h-full bg-base">
        <ChatInterfaceWrapper isRightPanelShown={isRightPanelShown} />
      </div>
    </div>
  );
}
