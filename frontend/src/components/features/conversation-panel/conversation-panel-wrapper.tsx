import ReactDOM from "react-dom";

interface ConversationPanelWrapperProps {
  isOpen: boolean;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

export function ConversationPanelWrapper({
  isOpen,
  onMouseEnter,
  onMouseLeave,
  children,
}: React.PropsWithChildren<ConversationPanelWrapperProps>) {
  if (!isOpen) return null;

  const portalTarget = document.getElementById("root-outlet");
  if (!portalTarget) return null;

  return ReactDOM.createPortal(
    <div
      className="absolute h-full w-full left-0 top-0 z-[9999]"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {children}
    </div>,
    portalTarget,
  );
}
