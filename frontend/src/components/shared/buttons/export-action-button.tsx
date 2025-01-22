interface ExportActionButtonProps {
  testId?: string;
  onClick: () => void;
  icon: React.ReactNode;
}

export function ExportActionButton({ testId, onClick, icon }: ExportActionButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testId}
      className="button-base p-1 hover:bg-neutral-500"
      title="Export trajectory"
    >
      {icon}
    </button>
  );
}
