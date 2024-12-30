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
            data-testid="arrow-back-icon"
          />
        ) : (
          <IoIosArrowForward
            size={20}
            className="text-neutral-400 hover:text-neutral-100 transition"
            data-testid="arrow-forward-icon"
          />
        )
      }
      testId="toggle"
      ariaLabel={isHidden ? "Open workspace" : "Close workspace"}
      onClick={onClick}
      className="absolute right-0 top-1/2 -translate-y-1/2 h-[100px] w-[20px] bg-neutral-800 hover:bg-neutral-700 rounded-l-md z-10"
    />
  );
}
