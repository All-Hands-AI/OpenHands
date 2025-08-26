import React from "react";
import { Branch } from "#/types/git";
import { cn } from "#/utils/utils";

interface BranchItemProps {
  branch: Branch;
  isHighlighted: boolean;
  isSelected: boolean;
  getItemProps: any;
  index: number;
}

export function BranchItem({
  branch,
  isHighlighted,
  isSelected,
  getItemProps,
  index,
}: BranchItemProps) {
  return (
    <li
      {...getItemProps({
        key: branch.name,
        index,
        item: branch,
        className: cn(
          "px-3 py-2 cursor-pointer text-sm border-b border-gray-100 last:border-b-0",
          "hover:bg-gray-50 focus:bg-gray-50 focus:outline-none",
          {
            "bg-blue-50 text-blue-700": isHighlighted,
            "bg-blue-100 text-blue-800 font-medium": isSelected,
          }
        ),
      })}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
            {branch.name}
          </span>
          {branch.protected && (
            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
              Protected
            </span>
          )}
        </div>
        <div className="text-xs text-gray-500">
          {branch.last_push_date && (
            <span>
              {new Date(branch.last_push_date).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>
      <div className="text-xs text-gray-400 mt-1 font-mono">
        {branch.commit_sha.substring(0, 8)}
      </div>
    </li>
  );
}