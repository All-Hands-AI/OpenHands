import React from "react";

interface EmptyStateProps {
  inputValue: string;
}

export function EmptyState({ inputValue }: EmptyStateProps) {
  return (
    <li
      className="px-3 py-2 text-gray-500 text-sm"
      data-testid="git-repo-dropdown-empty"
    >
      {inputValue ? "No repositories found" : "No repositories available"}
    </li>
  );
}