import ArrowUpCircleFillIcon from "#/icons/arrow-up-circle-fill.svg?react";
import { cn } from "#/utils/utils";

export interface ChatSendButtonProps {
  buttonClassName: string;
  handleSubmit: () => void;
  disabled: boolean;
}

export function ChatSendButton({
  buttonClassName,
  handleSubmit,
  disabled,
}: ChatSendButtonProps) {
  return (
    <button
      type="button"
      className={cn("size-[35px] cursor-pointer", buttonClassName)}
      data-name="arrow-up-circle-fill"
      data-testid="submit-button"
      onClick={handleSubmit}
      disabled={disabled}
    >
      <ArrowUpCircleFillIcon
        className="block max-w-none size-full"
        color="#959CB2"
      />
    </button>
  );
}
