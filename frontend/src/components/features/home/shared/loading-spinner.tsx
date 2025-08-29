import React from "react";
import { cn } from "#/utils/utils";

interface LoadingSpinnerProps {
  hasSelection: boolean;
  testId?: string;
}

export function LoadingSpinner({
  hasSelection,
  testId = "dropdown-loading",
}: LoadingSpinnerProps) {
  return (
    <div
      className={cn(
        "absolute top-1/2 transform -translate-y-1/2",
        hasSelection ? "right-16" : "right-12",
      )}
    >
      <div
        className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"
        data-testid={testId}
      />
    </div>
  );
}
