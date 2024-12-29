import { IoIosArrowForward, IoIosArrowBack } from "react-icons/io";
import { IconButton } from "./icon-button";

interface ToggleWorkspaceIconButtonProps {
  onClick: () => void;
  isHidden: boolean;
}

export function ToggleWorkspaceIconButton({
  onClick,
  isHidden,
}: ToggleWorkspaceIconButtonProps) {
  return (
    <IconButton
      icon={
        isHidden ? (
          <IoIosArrowBack
            size={20}
            className="text-neutral-400 hover:text-neutral-100 transition"
          />
        ) : (
          <IoIosArrowForward
            size={20}
            className="text-neutral-400 hover:text-neutral-100 transition"
          />
        )
      }
      testId="toggle"
      ariaLabel={isHidden ? "Open workspace" : "Close workspace"}
      onClick={onClick}
    />
  );
}
