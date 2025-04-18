import ReactDOM from "react-dom";

interface ConversationPanelWrapperProps {
  isOpen: boolean;
}

export function ConversationPanelWrapper({
  isOpen,
  children,
}: React.PropsWithChildren<ConversationPanelWrapperProps>) {
  if (!isOpen) return null;

  const portalTarget = document.getElementById("root-outlet");
  if (!portalTarget) return null;

  return ReactDOM.createPortal(
    <div className="absolute h-full w-full left-0 top-0 z-20 bg-black/80 rounded-xl">
      {children}
    </div>,
    portalTarget,
  );
}
