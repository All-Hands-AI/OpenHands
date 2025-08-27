import React from "react";

interface LoadingMoreStateProps {
  message?: string;
}

export function LoadingMoreState({
  message = "Loading more...",
}: LoadingMoreStateProps) {
  return (
    <li className="px-3 py-2 text-center text-sm text-[#B7BDC2] rounded-lg mx-0.5 my-0.5">{message}</li>
  );
}
