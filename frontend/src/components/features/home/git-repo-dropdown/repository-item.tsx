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
  getItemProps 
}: RepositoryItemProps) {
  return (
    <li
      key={repository.id}
      {...getItemProps({
        item: repository,
        index,
        className: cn(
          "px-3 py-2 cursor-pointer text-sm",
          "hover:bg-blue-50",
          highlightedIndex === index && "bg-blue-100",
          selectedItem?.id === repository.id && "bg-blue-200"
        ),
      })}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium">{repository.full_name}</span>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {repository.is_public ? (
            <span className="text-green-600">Public</span>
          ) : (
            <span className="text-orange-600">Private</span>
          )}
          {(repository.stargazers_count ?? 0) > 0 && (
            <span>⭐ {repository.stargazers_count}</span>
          )}
        </div>
      </div>
    </li>
  );
}