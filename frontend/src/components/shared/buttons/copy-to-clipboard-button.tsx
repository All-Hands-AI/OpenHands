import CheckmarkIcon from "#/icons/checkmark.svg?react";
import CopyIcon from "#/icons/copy.svg?react";

interface CopyToClipboardButtonProps {
  isHidden: boolean;
  isDisabled: boolean;
  onClick: () => void;
  mode: "copy" | "copied";
}

export function CopyToClipboardButton({
  isHidden,
  isDisabled,
  onClick,
  mode,
}: CopyToClipboardButtonProps) {
  return (
    <button
      hidden={isHidden}
      disabled={isDisabled}
      data-testid="copy-to-clipboard"
      type="button"
      onClick={onClick}
      className="button-base p-1 absolute top-1 right-1"
    >
      {mode === "copy" && <CopyIcon width={15} height={15} />}
      {mode === "copied" && <CheckmarkIcon width={15} height={15} />}
    </button>
  );
}
