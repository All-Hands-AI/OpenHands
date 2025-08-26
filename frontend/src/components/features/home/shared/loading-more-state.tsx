import React from "react";

interface LoadingMoreStateProps {
  message?: string;
}

export function LoadingMoreState({ message = "Loading more..." }: LoadingMoreStateProps) {
  return (
    <li className="px-3 py-2 text-center text-sm text-gray-500">
      {message}
    </li>
  );
}