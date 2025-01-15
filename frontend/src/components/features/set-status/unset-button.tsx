import { Tooltip } from "@nextui-org/react";
import { FaCircleXmark } from "react-icons/fa6";

interface UnsetButtonProps {
  testId?: string;
  onUnset: () => void;
}

export function UnsetButton({ testId, onUnset }: UnsetButtonProps) {
  return (
    <Tooltip content="Unset GitHub token">
      <button
        data-testid={testId}
        type="button"
        aria-label="Unset GitHub token"
        onClick={onUnset}
        className="text-[#A3A3A3] hover:text-[#FF4D4F]"
      >
        <FaCircleXmark size={16} />
      </button>
    </Tooltip>
  );
}
