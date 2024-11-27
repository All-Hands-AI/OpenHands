interface ScrollButtonProps {
  onClick: () => void;
  icon: JSX.Element;
  label: string;
  disabled?: boolean;
}

export function ScrollButton({
  onClick,
  icon,
  label,
  disabled = false,
}: ScrollButtonProps): JSX.Element {
  return (
    <button
      type="button"
      className="button-base relative text-xs px-2 py-1 cursor-pointer select-none"
      onClick={onClick}
      disabled={disabled}
    >
      <div className="flex items-center">
        {icon} <span className="inline-block">{label}</span>
      </div>
    </button>
  );
}
