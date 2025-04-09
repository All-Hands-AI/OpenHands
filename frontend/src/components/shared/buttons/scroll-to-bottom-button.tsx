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
      className="bg-neutral-1000 rounded text-neutral-100 dark:text-white dark:bg-neutral-300 p-1 rotate-180"
    >
      <ArrowSendIcon width={15} height={15} />
    </button>
  );
}
