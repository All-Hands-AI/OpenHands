import React from "react";
import EllipsisH from "#/assets/ellipsis-h.svg?react";
import CloudConnection from "#/assets/cloud-connection.svg?react";
import { ProjectMenu } from "./ProjectMenu";

export function ProjectMenuCard() {
  const [menuIsOpen, setMenuIsOpen] = React.useState(false);

  const toggleMenuVisibility = () => {
    setMenuIsOpen((prev) => !prev);
  };

  return (
    <div className="px-4 py-[10px] w-[337px] rounded-xl border border-[#525252] flex justify-between items-center relative">
      {menuIsOpen && <ProjectMenu />}
      <div className="flex flex-col">
        <span className="text-sm leading-6 font-semibold">New Project</span>
        <span className="text-xs leading-4 text-[#A3A3A3] flex items-center gap-2">
          Connect to GitHub
          <CloudConnection width={12} height={12} />
        </span>
      </div>
      <button
        type="button"
        onClick={toggleMenuVisibility}
        aria-label="Open project menu"
      >
        <EllipsisH width={36} height={36} />
      </button>
    </div>
  );
}
