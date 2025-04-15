import { FaEllipsisV } from "react-icons/fa";

interface EllipsisButtonProps {
  onClick: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

export function EllipsisButton({ onClick }: EllipsisButtonProps) {
  return (
    <button data-testid="ellipsis-button" type="button" onClick={onClick}>
      <FaEllipsisV fill="#a3a3a3" />
    </button>
  );
}
