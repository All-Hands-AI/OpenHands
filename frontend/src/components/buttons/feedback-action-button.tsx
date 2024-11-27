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
      className="button-base p-1 hover:bg-neutral-500"
    >
      {icon}
    </button>
  );
}
