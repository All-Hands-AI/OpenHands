import ArrowSendIcon from "#/icons/arrow-send.svg?react";

interface SubmitButtonProps {
  isDisabled?: boolean;
  onClick: () => void;
}

export function SubmitButton({ isDisabled, onClick }: SubmitButtonProps) {
  return (
    <button
      aria-label="Send"
      disabled={isDisabled}
      onClick={onClick}
      type="submit"
      className="border border-white rounded-lg w-6 h-6 hover:bg-neutral-500 focus:bg-neutral-500 flex items-center justify-center"
    >
      <ArrowSendIcon />
    </button>
  );
}
