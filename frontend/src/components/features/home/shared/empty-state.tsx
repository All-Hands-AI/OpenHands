import React from "react";

interface EmptyStateProps {
  inputValue: string;
  searchMessage?: string;
  emptyMessage?: string;
  testId?: string;
}

export function EmptyState({ 
  inputValue, 
  searchMessage = "No items found",
  emptyMessage = "No items available",
  testId = "dropdown-empty"
}: EmptyStateProps) {
  return (
    <li
      className="px-3 py-2 text-gray-500 text-sm"
      data-testid={testId}
    >
      {inputValue ? searchMessage : emptyMessage}
    </li>
  );
}