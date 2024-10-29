import ArrowSendIcon from "#/assets/arrow-send.svg?react";

interface ScrollToBottomButtonProps {
  onClick: () => void;
}

export function ScrollToBottomButton({ onClick }: ScrollToBottomButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid="scroll-to-bottom"
      className="p-1 bg-neutral-700 border border-neutral-600 rounded hover:bg-neutral-500 rotate-180"
    >
      <ArrowSendIcon width={15} height={15} />
    </button>
  );
}
