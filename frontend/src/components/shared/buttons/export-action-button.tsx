interface ExportActionButtonProps {
  onClick: () => void;
  icon: React.ReactNode;
}

export function ExportActionButton({ onClick, icon }: ExportActionButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="button-base p-1 hover:bg-neutral-500"
      title="Export trajectory"
    >
      {icon}
    </button>
  );
}
