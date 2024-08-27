import React from "react";

interface ProjectMenuListItemProps {
  children: string;
}

export function ProjectMenuListItem({ children }: ProjectMenuListItemProps) {
  return (
    <li className="text-sm px-4 py-2 hover:bg-white/10 first-of-type:rounded-t-md last-of-type:rounded-b-md">
      <button type="button">{children}</button>
    </li>
  );
}
