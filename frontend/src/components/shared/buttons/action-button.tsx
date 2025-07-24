import { Tooltip } from "@heroui/react";
import { AgentState } from "#/types/agent-state";

interface ActionButtonProps {
  isDisabled?: boolean;
  content: string;
  action: AgentState;
  handleAction: (action: AgentState) => void;
  variant?: "default" | "prominent";
}

export function ActionButton({
  isDisabled = false,
  content,
  action,
  handleAction,
  variant = "default",
  children,
}: React.PropsWithChildren<ActionButtonProps>) {
  const baseClasses =
    "relative overflow-visible cursor-default hover:cursor-pointer group disabled:cursor-not-allowed transition-colors duration-300 ease-in-out border rounded-full p-1";

  const variantClasses = {
    default: "border-transparent hover:border-red-400/40",
    prominent:
      "border-transparent hover:border-red-400/40 bg-gray-600/50 hover:bg-gray-600/70",
  };

  return (
    <Tooltip content={content} closeDelay={100}>
      <button
        onClick={() => handleAction(action)}
        disabled={isDisabled}
        className={`${baseClasses} ${variantClasses[variant]}`}
        type="button"
      >
        <span className="relative group-hover:filter group-hover:drop-shadow-[0_0_5px_rgba(255,64,0,0.4)]">
          {children}
        </span>
      </button>
    </Tooltip>
  );
}
