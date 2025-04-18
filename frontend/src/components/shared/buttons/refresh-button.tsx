import Refresh from "#/icons/refresh.svg?react";

interface RefreshButtonProps {
  onClick: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

export function RefreshButton({ onClick }: RefreshButtonProps) {
  return (
    <button type="button" onClick={onClick}>
      <Refresh width={14} height={14} />
    </button>
  );
}
