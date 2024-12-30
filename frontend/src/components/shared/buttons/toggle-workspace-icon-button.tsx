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
          <IoIosArrowForward
            size={20}
            className="text-neutral-400 hover:text-neutral-100 transition"
            data-testid="arrow-forward-icon"
          />
        ) : (
          <IoIosArrowBack
            size={20}
            className="text-neutral-400 hover:text-neutral-100 transition"
            data-testid="arrow-back-icon"
          />
        )
      }
      testId="toggle"
      ariaLabel={isHidden ? "Open workspace" : "Close workspace"}
      onClick={onClick}
      className="absolute right-0 top-1/2 transform -translate-y-1/2 h-[100px] w-[20px] bg-neutral-800 hover:bg-neutral-700 rounded-l-md"
    />
  );
}
