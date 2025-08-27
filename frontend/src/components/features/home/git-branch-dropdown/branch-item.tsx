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
          "px-3 py-2 cursor-pointer text-sm rounded-lg mx-0.5 my-0.5",
          "text-[#ECEDEE] focus:outline-none",
          {
            "bg-[#24272E]": isHighlighted && !isSelected,
            "bg-[#C9B974] text-black": isSelected,
            "hover:bg-[#24272E]": !isSelected,
            "hover:bg-[#C9B974] hover:text-black": isSelected,
          },
        ),
      })}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span
            className={cn(
              "font-mono text-xs px-2 py-1 rounded",
              isSelected
                ? "bg-black/20 text-black"
                : "bg-[#24272E] text-[#ECEDEE]",
            )}
          >
            {branch.name}
          </span>
          {branch.protected && (
            <span
              className={cn(
                "text-xs px-2 py-1 rounded",
                isSelected
                  ? "bg-yellow-600 text-white"
                  : "bg-yellow-100 text-yellow-800",
              )}
            >
              Protected
            </span>
          )}
        </div>
        <div
          className={cn(
            "text-xs",
            isSelected ? "text-black/70" : "text-[#B7BDC2]",
          )}
        >
          {branch.last_push_date && (
            <span>{new Date(branch.last_push_date).toLocaleDateString()}</span>
          )}
        </div>
      </div>
      <div
        className={cn(
          "text-xs mt-1 font-mono",
          isSelected ? "text-black/70" : "text-[#B7BDC2]",
        )}
      >
        {branch.commit_sha.substring(0, 8)}
      </div>
    </li>
  );
}
