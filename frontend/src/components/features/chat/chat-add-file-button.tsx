import PaperclipIcon from "#/icons/paper-clip.svg?react";

export interface ChatAddFileButtonProps {
  handleFileIconClick: () => void;
}

export function ChatAddFileButton({
  handleFileIconClick,
}: ChatAddFileButtonProps) {
  return (
    <div
      className="h-[25px] relative shrink-0 w-[13px] cursor-pointer transition-all duration-200 hover:scale-110 active:scale-95"
      data-name="Shape"
      data-testid="paperclip-icon"
      onClick={handleFileIconClick}
    >
      <PaperclipIcon
        className="block max-w-none w-[13px] h-[25px]"
        color="#959CB2"
      />
    </div>
  );
}
