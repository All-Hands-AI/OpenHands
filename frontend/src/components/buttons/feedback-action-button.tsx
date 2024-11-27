interface FeedbackActionButtonProps {
  testId?: string;
  onClick: () => void;
  icon: React.ReactNode;
}

export function FeedbackActionButton({
  testId,
  onClick,
  icon,
}: FeedbackActionButtonProps) {
  return (
    <button
      type="button"
      data-testid={testId}
      onClick={onClick}
      className="p-1 bg-neutral-700 border border-neutral-600 rounded hover:bg-neutral-500"
    >
      {icon}
    </button>
  );
}
