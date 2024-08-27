import React from "react";
import { ProjectMenuListItem } from "./ProjectMenuListItem";

export function ProjectMenu() {
  return (
    <ul className="bg-[#404040] rounded-md w-[224px] absolute right-0 bottom-[calc(100%+8px)]">
      <ProjectMenuListItem>Connect to GitHub</ProjectMenuListItem>
      <ProjectMenuListItem>Reset Workspace</ProjectMenuListItem>
      <ProjectMenuListItem>Download as .zip</ProjectMenuListItem>
    </ul>
  );
}
