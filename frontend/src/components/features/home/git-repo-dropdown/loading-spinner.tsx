import React from "react";
import { cn } from "#/utils/utils";
import { GitRepository } from "#/types/git";

interface LoadingSpinnerProps {
  selectedRepository: GitRepository | null;
}

export function LoadingSpinner({ selectedRepository }: LoadingSpinnerProps) {
  return (
    <div className={cn(
      "absolute top-1/2 transform -translate-y-1/2",
      selectedRepository ? "right-16" : "right-12"
    )}>
      <div
        className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"
        data-testid="git-repo-dropdown-loading"
      />
    </div>
  );
}