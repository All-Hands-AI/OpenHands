import { IoIosRefresh } from "react-icons/io";
import { IconButton } from "./icon-button";

interface RefreshIconButtonProps {
  onClick: () => void;
}

export function RefreshIconButton({ onClick }: RefreshIconButtonProps) {
  return (
    <IconButton
      icon={
        <IoIosRefresh
          size={16}
          className="text-neutral-400 hover:text-neutral-100 transition"
        />
      }
      testId="refresh"
      ariaLabel="Refresh workspace"
      onClick={onClick}
    />
  );
}
