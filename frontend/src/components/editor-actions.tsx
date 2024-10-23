import { cn } from "@nextui-org/react";
import { HTMLAttributes } from "react";

interface EditorActionButtonProps {
  onClick: () => void;
  disabled: boolean;
  className: HTMLAttributes<HTMLButtonElement>["className"];
}

function EditorActionButton({
  onClick,
  disabled,
  className,
  children,
}: React.PropsWithChildren<EditorActionButtonProps>) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "text-sm py-0.5 rounded w-20",
        "hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed",
        className,
      )}
    >
      {children}
    </button>
  );
}

interface EditorActionsProps {
  onSave: () => void;
  onDiscard: () => void;
  isDisabled: boolean;
}

export function EditorActions({
  onSave,
  onDiscard,
  isDisabled,
}: EditorActionsProps) {
  return (
    <div className="flex gap-2">
      <EditorActionButton
        onClick={onSave}
        disabled={isDisabled}
        className="bg-neutral-800 disabled:hover:bg-neutral-800"
      >
        Save
      </EditorActionButton>

      <EditorActionButton
        onClick={onDiscard}
        disabled={isDisabled}
        className="border border-neutral-800 disabled:hover:bg-transparent"
      >
        Discard
      </EditorActionButton>
    </div>
  );
}
