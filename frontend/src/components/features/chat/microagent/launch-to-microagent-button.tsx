import { FaCircleUp } from "react-icons/fa6";

interface LaunchToMicroagentButtonProps {
  onClick: () => void;
}

export function LaunchToMicroagentButton({
  onClick,
}: LaunchToMicroagentButtonProps) {
  return (
    <button
      data-testid="launch-microagent-button"
      type="button"
      onClick={onClick}
      className="w-7 h-7 border border-white/30 bg-white/20 rounded flex items-center justify-center"
    >
      <FaCircleUp className="w-[14px] h-[14px]" />
    </button>
  );
}
