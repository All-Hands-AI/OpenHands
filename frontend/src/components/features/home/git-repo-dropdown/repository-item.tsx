import React from "react";
import { cn } from "#/utils/utils";
import { GitRepository } from "#/types/git";

interface RepositoryItemProps {
  repository: GitRepository;
  index: number;
  highlightedIndex: number;
  selectedItem: GitRepository | null;
  getItemProps: any;
}

export function RepositoryItem({
  repository,
  index,
  highlightedIndex,
  selectedItem,
  getItemProps,
}: RepositoryItemProps) {
  return (
    <li
      key={repository.id}
      {...getItemProps({
        item: repository,
        index,
        className: cn(
          "px-3 py-2 cursor-pointer text-sm rounded-lg mx-0.5 my-0.5",
          "text-[#ECEDEE] focus:outline-none",
          {
            "bg-[#24272E]":
              highlightedIndex === index && selectedItem?.id !== repository.id,
            "bg-[#C9B974] text-black": selectedItem?.id === repository.id,
            "hover:bg-[#24272E]": selectedItem?.id !== repository.id,
            "hover:bg-[#C9B974] hover:text-black":
              selectedItem?.id === repository.id,
          },
        ),
      })}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium">{repository.full_name}</span>
        <div
          className={cn(
            "flex items-center gap-2 text-xs",
            selectedItem?.id === repository.id
              ? "text-black/70"
              : "text-[#B7BDC2]",
          )}
        >
          {repository.is_public ? (
            <span
              className={cn(
                selectedItem?.id === repository.id
                  ? "text-green-800"
                  : "text-green-400",
              )}
            >
              Public
            </span>
          ) : (
            <span
              className={cn(
                selectedItem?.id === repository.id
                  ? "text-orange-800"
                  : "text-orange-400",
              )}
            >
              Private
            </span>
          )}
          {(repository.stargazers_count ?? 0) > 0 && (
            <span>⭐ {repository.stargazers_count}</span>
          )}
        </div>
      </div>
    </li>
  );
}
