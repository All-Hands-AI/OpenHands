import { cn } from "#/utils/utils";
import CloudConnection from "#/assets/cloud-connection.svg?react";

interface ProjectMenuDetailsPlaceholderProps {
  isConnectedToGitHub: boolean;
  onConnectToGitHub: () => void;
}

export function ProjectMenuDetailsPlaceholder({
  isConnectedToGitHub,
  onConnectToGitHub,
}: ProjectMenuDetailsPlaceholderProps) {
  return (
    <div className="flex flex-col">
      <span className="text-sm leading-6 font-semibold">New Project</span>
      <button
        type="button"
        onClick={onConnectToGitHub}
        disabled={isConnectedToGitHub}
      >
        <span
          className={cn(
            "text-xs leading-4 text-[#A3A3A3] flex items-center gap-2",
            "hover:underline hover:underline-offset-2",
          )}
        >
          {!isConnectedToGitHub ? "Connect to GitHub" : "Connected"}
          <CloudConnection width={12} height={12} />
        </span>
      </button>
    </div>
  );
}
