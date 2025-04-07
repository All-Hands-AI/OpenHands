interface TrajectoryActionButtonProps {
  testId?: string;
  onClick: () => void;
  icon: React.ReactNode;
}

export function TrajectoryActionButton({
  testId,
  onClick,
  icon,
}: TrajectoryActionButtonProps) {
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
