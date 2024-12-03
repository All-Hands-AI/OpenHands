interface DeleteButtonProps {
  onClick: () => void;
}

export function DeleteButton({ onClick }: DeleteButtonProps) {
  return (
    <button
      data-testid="delete-button"
      type="button"
      onClick={onClick}
      className="w-6 h-6"
    >
      D
    </button>
  );
}
