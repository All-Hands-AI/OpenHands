import { IoEllipsisVertical } from "react-icons/io5";

interface EllipsisButtonProps {
  onClick: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

export function EllipsisButton({ onClick }: EllipsisButtonProps) {
  return (
    <button data-testid="ellipsis-button" type="button" onClick={onClick}>
      <IoEllipsisVertical fill="#494949" />
    </button>
  );
}
