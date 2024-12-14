import ArrowSendIcon from "#/icons/arrow-send.svg?react";

interface ScrollToBottomButtonProps {
  onClick: () => void;
}

export function ScrollToBottomButton({ onClick }: ScrollToBottomButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid="scroll-to-bottom"
      className="button-base p-1 hover:bg-neutral-500 rotate-180"
    >
      <ArrowSendIcon width={15} height={15} />
    </button>
  );
}
