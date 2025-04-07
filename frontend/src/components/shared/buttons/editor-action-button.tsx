import { cn } from "#/utils/utils";

interface EditorActionButtonProps {
  onClick: () => void;
  disabled: boolean;
  className: React.HTMLAttributes<HTMLButtonElement>["className"];
}

export function EditorActionButton({
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
